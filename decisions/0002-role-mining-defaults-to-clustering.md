# 0002. Role mining defaults to clustering, not attribute grouping

**Status:** decided, shipped
**Area:** `engine/`
**Headline:** F1 **0.06** to **0.82** from changing one default

## The question

Role mining works by grouping people who ought to look alike, then looking for
the entitlement bundle they share. How should the groups be formed?

Two options were implemented: **attribute grouping** (group by department and
title, which is cheap, obvious, and explainable to a client) and **clustering**
(agglomerative clustering over access vectors, which is more expensive and less
immediately explainable).

Attribute grouping shipped as the default, because it is the intuitive answer and
it is what a consultant does by hand.

## What the measurement said

Scored against the synthetic generator's planted ground-truth roles:

| Grouping | F1 |
|---|---|
| attribute | **0.06** |
| clustering | **0.82** |

Not a tuning difference. A structural one.

## Why

A department contains **several** roles. Finance has accounts-payable people,
financial analysts, and controllers, and they hold materially different access.
Attribute grouping puts all of them in one group, and the pipeline recovers at
most one bundle per group. So the ceiling is not "clustering is somewhat better,"
it is that attribute grouping can only ever find one of the several roles
actually present, and it will find a blurred average of them rather than any real
one.

This also explained a separate mystery that had been open for weeks. On one seed,
the small tier produced **zero** candidate roles even at permissive thresholds,
which looked like a coverage bug. It was not. A low coverage floor unions an
entire department's roles into one oversized bundle, that bundle overflows
`max_entitlements_per_role`, and it gets silently dropped. 38 of 48 groups were
being discarded that way. The same seed yields 47 candidates under clustering.

## The tell

The §8 accuracy gate was already passing its F1 threshold before this change.

It passed because the gate **forced clustering** by way of the peer-group view's
method, rather than running the shipped default. The product's out-of-the-box
behavior was never what the gate measured. That is the tell, and it is worth
stating plainly: a quality gate that does not exercise the shipped defaults is
measuring a configuration nobody runs.

The gate now runs the default unopened, and clears the 0.75 threshold. The
attribute path stays exercised but is deliberately not gated, since it
structurally scores about 0.06 and gating it would only encode the bug.

## The subtlety in the fix

The obvious fix, flipping the peer-group default globally, would have been wrong.
Attribute grouping is still the right default for the peer-group **view** and for
outlier scoring, where "compared against people with your job title" is exactly
the comparison a reviewer wants, and where explainability matters more than
recall.

So mining got its own `grouping_method` parameter, resolved independently of the
view's. The pipeline builds mining's grouping separately and **reuses** the view's
groups only when the two methods coincide, so a matched-method run stays
byte-identical and pays no second O(n²) pass.

That this change is genuinely mining-only was proven rather than asserted: an
invariance test shows the flip moves no outlier and no SoD finding, and the
outlier golden file's findings block is byte-identical, with only the recorded
`params` gaining the one new field.

## In hindsight

The intuitive grouping was wrong by a factor of thirteen, and it survived because
the gate was quietly configured around it. Ground truth is what caught it. This
is the strongest argument for having built the
[synthetic generator](../synthgen/) first: an
algorithm scoring 0.06 looks perfectly reasonable in a UI, and no amount of
eyeballing candidate roles would have revealed it.
