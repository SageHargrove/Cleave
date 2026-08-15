# 0006. Comparability is a precondition, not a convenience

**Status:** decided, shipped
**Area:** `engine/`, `core/`
**Found by:** security review, before merge

## The setup

Cleave keeps analysis runs so it can tell a client what changed. Part of that is
resolution: a finding present in the previous run and absent from the current one
has presumably been remediated, so it gets written back as `resolved`. That is a
genuinely useful feature. "You fixed 400 things this quarter" is exactly what a
consultant wants on a slide.

## The defect

[Decision 0007](0007-the-threshold-was-the-fix.md) raised the outlier score
threshold from 0.0 to 0.80, which removed about 87% of emitted findings as
intended.

On the **first run after upgrading**, resolution logic would have compared the new
filtered run against the old unfiltered one, found roughly **85% of prior findings
missing**, and reported them all as remediated. It would then have written them
back as resolved rows, reinstating exactly the volume of data the change existed
to remove, and telling the customer they had fixed 170,000 access problems
overnight.

Nobody remediated anything. A default changed.

This was caught in security review of the diff, before merge.

## The fix

Resolution now requires a **comparable** run. Two runs are comparable when their
recorded parameters match, excluding counts. A threshold change, a grouping-method
change, or a scope change all make runs incomparable, and incomparable runs
produce no resolutions at all rather than a wrong number.

The same guard covers two other cases that would have failed identically:

- **Scoped analysis.** A run scoped to one business unit and a full-estate run
  are not comparable. Measured against the scoped path, this guard holds
  resolutions at exactly **zero** where the naive comparison would have declared
  the entire out-of-scope estate remediated.
- **SoD rule-set changes.** Removing a rule is not the same as people no longer
  violating it.

## Why this is the interesting kind of bug

It is invisible in every way a bug can be invisible. It does not crash, it does
not throw, it does not log, and no test asserting "resolution works" would fail,
because resolution *did* work exactly as specified. The specification was
incomplete.

It is also a bug whose output is **more pleasant than the truth**. It reports good
news. A user's instinct on seeing "170,000 findings resolved" after an upgrade is
satisfaction rather than suspicion, so it could have survived a long time in
production, quietly corrupting every historical comparison.

The general principle worth extracting: whenever two artifacts are compared, the
precondition that they are *comparable* deserves to be encoded and enforced. It is
almost never stated in the requirement, because it is too obvious to write down,
and it is exactly the thing a parameter change silently violates.
