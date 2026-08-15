# 0003. Retention shipped at N=2, not the designed N=10

**Status:** decided, shipped
**Area:** `core/`, `report/`

## The design

Analysis runs are immutable and comparable over time, so keeping history is
valuable: you want to show a client what changed between March and June. The
design specified retaining the last **10** runs, on the stated premise that the
findings tier is small relative to the underlying access data.

That premise was written down as a premise, which is the only reason it got
checked.

## What the measurement said

One analysis run emits roughly **one finding per effective-access row**.
Measured at the small tier: 203,885 findings against 202,806 effective-access
rows.

At about **297 MiB per retained run**, N=10 would have made retained history
**164% of the project file**. The file a consultant emails to a client would have
been more than half old findings.

The premise was simply false. Findings are not a thin summary layer on top of the
access data, they are the same order of magnitude as it, because the analysis
emits a judgment about nearly every access relationship it examines.

## The decision

Ship N=2.

Later work cut per-run cost by 7.1× (see
[0007](0007-the-threshold-was-the-fix.md)), which would have made N≈14 affordable.
It stayed at 2 anyway, and the reasoning changed from emergency to deliberate:
**N multiplies a per-run quantity that still scales with project size, and
nothing in the product consumes more than one predecessor.** Drift comparison
needs the previous run. It does not need the previous nine. Retaining data that
nothing reads, at a cost that grows with the customer's estate, is a liability
rather than a feature.

## What made this cheap

The change was a **one-constant edit**, which is exactly what making retention
configurable was for. The design's real contribution was not the number 10, it
was arranging things so the number could be wrong without costing anything.

Getting the number wrong was fine. Hardcoding it would not have been.

## In hindsight

Worth separating two things that are easy to conflate. The design was wrong about
the size of the findings tier, and that was a genuine miss, catchable earlier by
estimating one finding per access row on paper before writing the retention code.

But the design was right about the shape: one tunable constant, measured after
the fact. That is what made the miss a five-minute fix instead of a
re-architecture.
