# 0007. The right defect for the wrong reason

**Status:** decided, shipped
**Area:** `engine/`

## The symptom

Outlier scoring was emitting roughly **one finding per effective-access row**.
At the small tier that meant 202,806 findings and a 238 MiB findings tier per
run. Analysis took 94 seconds. At full tier it was one of the things making runs
impossible to complete.

An outlier detector that flags nearly everything is not detecting outliers.

## The diagnosis in the proposal

The change proposal blamed a strict `<` comparison letting zero-rarity findings
survive the filter. Plausible, specific, and the kind of off-by-one that causes
exactly this symptom.

It was wrong.

## What the data said

Not one finding at the small tier scores 0.0. The minimum observed score is
**0.198** and the median is **0.694**.

So the proposed fix, correcting the comparison operator, would have removed
**nothing**. It would have shipped, the symptom would have persisted, and the
next person would have started from a diagnosis that had already been marked as
addressed.

The actual defect was that the threshold's *value* was 0.0. Not the comparison
against it. The filter was admitting everything because it had been configured to
admit everything.

## The fix

`outlier_min_score` moved from 0.0 to **0.80**, derived rather than picked: the
highest threshold that still retains **100% of planted outliers** across four
generated companies.

| | before | after |
|---|---|---|
| Findings (small tier) | 202,806 | **25,708** |
| Findings tier per run | 238.3 MiB | **33.4 MiB** |
| Analysis wall time | 94.1 s | **36.5 s** |

Cost fell 7.1×, and no planted outlier was lost.

## The gate had to change too, and that needed care

The §8 accuracy gate scored rank quality as a **fraction** of the emitted list.
Filtering the list shrinks the denominator, so the same absolute ranks score
differently: 0.962 fell to 0.769 for purely arithmetic reasons, with no finding
having moved.

That is a case where a metric moving looks like a regression and is not. The gate
now counts **rows** (5,000, calibrated to reproduce the pre-filter figure exactly)
and adds a direct recall assertion, so the number means the same thing before and
after.

Two guards keep the old behavior from returning silently: a ratio assertion on
findings-per-access-row, and the comparability precondition in
[0006](0006-comparability-as-a-precondition.md), which this change's fallout made
necessary.

## The related memory rewrite

Thresholding fixed what got **written**. It did not fix what got **built**:
scoring still constructed a contribution breakdown for every pair before applying
the threshold, so the corpus-wide accumulator sized with the estate regardless.

The rewrite made scoring identity-major. A pre-pass keeps per-group holder counts,
then each pair's breakdown is built one at a time and discarded unless it clears
the threshold. The corpus-wide accumulator no longer exists, so the threshold now
bounds what is **held**, not merely what is written.

Measured on identical data: peak RSS 3.93 GB to **2.36 GB**, memory exponent 1.15
to 0.89. Per-pair shape 574 bytes to 88.

Proving it changed nothing mattered more than the speedup. The old algorithm was
frozen into a reference module and the new one shown equal across four companies,
a threshold and cap sweep, risk overrides, and overlapping groupings, plus a
pinned golden file. The `tracemalloc` shape guard was written to **fail against
the old algorithm**, so it demonstrably guards something.

Worth noting that the design sketch for this rewrite ("keep two running floats per
pair") was superseded during implementation. The per-pair accumulator turned out
not to be needed at all.

## In hindsight

Two lessons, and the second is the one that generalizes.

A plausible root cause that explains the symptom is not the same as the root
cause. Both stories predicted the observed behavior. Only one survived contact
with the score distribution, and checking took one query.

And a fix that removes 87% of your output is not finished when the output shrinks.
It is finished when you have found what else was reading that output. Here it was
the accuracy gate's denominator and the resolution comparison, and both were
wrong in ways that looked like success.
