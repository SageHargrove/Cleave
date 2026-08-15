# 0005. NFR-2 is unmet at full scale

**Status:** open, documented
**Area:** `engine/`, `core/`

This entry documents a target the product currently **fails**. It is here because
a decision record that only contains wins is a marketing page.

## The target

NFR-2: a 50,000-identity estate, roughly 5 million assignments, analyzed within
15 minutes and 16 GB of memory.

## What actually happened

The first three attempts at a full-tier run **never finished**. Each was lost
mid-analysis holding 15 to 18 GB.

Because no full run completed, the budget could not be measured directly, so it
was attributed from a **scaling series** instead, following the convention the
existing performance tests already used. That projection said roughly 101 minutes
and 55 GB.

That projection was published with an explicit warning that it extrapolated 10×
beyond a 5× measured span and should be read as an order of magnitude rather than
a figure. That warning turned out to be worth writing: the projection was wrong.

## The first completed full run

After the memory work in [0007](0007-the-threshold-was-the-fix.md) and an
identity-major rewrite of outlier scoring, a full-tier run completed analysis and
persistence for the first time:

| | |
|---|---|
| Assignments imported | 3,790,000 (10.5 min) |
| Effective access rows | **20,220,837** (5.34× expansion) |
| Outlier scoring | 31.5 min, +3.7 GB |
| Peak RSS | **24.37 GB** |
| Budget | 15 min, 16 GB |

So the real figure is about **1.5× over on memory**, not the projected 3.4×. The
projection was pessimistic by more than a factor of two, which is a useful
calibration on scaling-series extrapolation: it was directionally right and
quantitatively poor.

Persistence is measured in **hours**, which is the actual wall.

## What is actually binding

Two things, in order.

**1. Persistence.** At full tier, persistence wrote an approximately 40 GB
write-ahead log over hours of active time, and the final durable checkpoint alone
exceeded 75 minutes while degrading the whole machine, before being killed. Batch
sizing, index maintenance during bulk insert, rewriting effective access in full
every run, and checkpoint strategy are all implicated. This is the dominant cost
and the next piece of work.

**2. Effective-access materialization.** 20.2 million rows and **18.47 GB peak
RSS before scoring even begins.** Expansion is superlinear across the series
(2.50× to 3.46× to 4.14× to 5.34×), which the series predicted correctly.

Note that the engine's earlier conclusion, "full recompute per run is viable, about
100 seconds at 5M," came from a fixed-shape fixture. Measured on real generator
output the stage took 172 seconds, so the *time* estimate held. Its **memory** is
what the budget dies on, and memory was not what that fixture was measuring.

## Caveats recorded honestly

The persistence wall-clock figure is polluted by the machine sleeping partway
through. The final checkpoint was operator-killed after 75+ minutes of awake time
because of machine-wide I/O lag, so the export read-back count was never taken.

Separately, one previously-archived measurement (the 0.02 fraction row) proved
**irreproducible**, because the script that produced it was never checked in. The
0.05 and 0.10 rows reproduced exactly. The harness is now checked in as
`tests/scale_runner.py` with a `--reference` flag for dual-run comparison against
a frozen copy of the old algorithm, which is what let the memory rewrite be proven
bit-identical rather than assumed.

## Why it is stated this way

Nothing in the repository, the site, or the reports claims the 5M tier works.

The tiers below it are measured and do work: import at 2.1 minutes against a 10
minute budget, and access-explorer queries at 5.3 / 5.3 / 21.3 ms against a 500 ms
budget. Those numbers are real, and they stay credible precisely because the one
that is not is written down next to them.

## Adjacent measurement worth keeping

Explorer performance had a genuine planner trap. SQLite was driving the
`identity_access` join from the wrong table for lack of `ANALYZE` statistics.
Forcing a two-step took it from **347 ms to 2.8 ms**. Worth knowing before
concluding a query is inherently expensive.
