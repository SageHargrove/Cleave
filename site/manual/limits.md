# Limits

After this page you know what Cleave does not do yet, with the numbers, before a client asks.

Everything here is a measured or designed-in fact about the current version,
stated so that you meet it in this document rather than in front of a client.
Where a number is given, the date it was measured is given with it.

## Scale

**Cleave's stated target of 50,000 identities is not met by this version.**
The target (50,000 identities, 25,000 entitlements, 5,000,000 assignments,
analysed in under 15 minutes on a 16 GB laptop) is what the product is designed
toward. What has been measured:

- **2026-07-21**: three attempts at that scale did not complete; each was lost
  mid-analysis holding 15 to 18 GB. Time and memory were projected from a
  scaling series at roughly 100 minutes and 55 GB, as an order of magnitude.
- **2026-07-22**: the first run at that scale to complete analysis. 3.79 million
  assignments imported in 10.5 minutes; effective access materialised to
  20.2 million rows (a 5.3× expansion); scoring took 31.5 minutes; **peak memory
  24.37 GB** against the 16 GB budget. Persistence of the results was still
  running after 75 minutes, degrading the machine, and was stopped. The
  materialisation of effective access is the binding memory stage (18.5 GB
  before scoring begins), and persistence is the wall.

So: **the 500 to 5,000-identity engagement is unaffected**, and is what the
product is measured and tuned on (the sample is 2,000; see
[How long it takes](analysis.md#how-long-it-takes)). Ten to twenty thousand
identities will run, in minutes and gigabytes rather than seconds, and scoping
the run by application or department is the tool for it. Do not take on the
50,000 tier expecting this version to finish; say so, and use scope.

Import at that scale is fine (2.1 minutes against a 10-minute budget on the
2026-07-21 run) and browsing is fast at every measured scale (Explorer queries
in 5 to 21 ms against a 500 ms budget). It is analysis and its persistence that
do not yet fit.

## Roles are candidates

Role mining produces candidate roles, not roles, and there is nowhere in Cleave
to turn one into the other. On the sample estate at shipped defaults it emits
on the order of fifty candidates, some carrying nearly a hundred entitlements;
nobody ships those untouched, and today the shaping (rename, drop entitlements,
split, merge) happens in Excel or in the IGA suite after export
([Candidate roles](findings.md#candidate-roles)). The IGA export sends the
candidate as mined. In-tool refinement, with the operator's decisions kept
separately from the run so they survive re-mining, is the next planned
capability; it does not exist yet.

## The outlier score and peer-group size

The score is a fraction of the peer group, so ranking by score selects the
largest groups first: one holder in 417 scores 0.9976, one holder in 12 scores
0.9167. This is by construction and was deliberately not normalised away
([Peer-group size](findings.md#peer-group-size)). The report and the views are
built around it (population first, one example per group), and you should
present the same way. What Cleave cannot yet tell you is a calibrated *precision*
for outliers: on the synthetic estates it is measured against, the noise grants
are statistically identical to the planted outliers, so the accuracy gate
measures how well the score *ranks* known outliers (pooled recall in the top 5%
of 0.962 on the 2,000-identity generator estate) and not how many of the top
findings are "real". Treat the list as a ranked review queue, not a verdict.

## Dormancy

Dormancy findings exist only when a source supplied last-login data. When none
does, the run says `dormancy_not_checked` and produces no dormancy findings; an
empty dormancy list on such a run means the check did not run
([Warnings](analysis.md#warnings)). Cleave cannot infer last login from
anything else and does not try. The same honesty applies to terminated-with-
access, which keys on a termination date: identities with a terminated status
and no date are counted in a warning and not checked.

## SoD templates

Separation-of-duties rules ship as templates that name entitlements the way a
textbook does, not the way your client's catalogue does. Nothing is enabled
until you seed the templates, map each side to real entitlement names, and turn
the rule on; a rule change takes effect on the next run
([Separation of duties](findings.md#separation-of-duties)). A fresh project
therefore shows no SoD findings, and that is not a clean bill of health.

## Scoped runs

A run scoped to applications or departments computes rarity among the peers in
scope and is recorded as scoped. It is not comparable to a full run or to a
differently scoped one, and it never resolves findings outside its scope
([Scope](analysis.md#scope)). Compare like with like.

## Excel row cap

The access-matrix sheet in the Excel export stops at the worksheet row limit
and says so in its last row; the full matrix is in the CSV and JSON exports.
No other sheet is capped ([Excel](reports.md#excel)).

## IIQ bundle names

The SailPoint IIQ role export uses the candidate role's name as the `<Bundle>`
name, which IIQ treats as the object's unique key. Two candidates exported
with the same name would collide on import. Check names before importing
([IGA role export](reports.md#iga-role-export)).

## AI assistance

Cleave contains an optional AI layer (enrichment of entitlement descriptions,
plain-language explanations of findings, help with column mapping, and
natural-language queries) with three provider modes: none, a local
OpenAI-compatible endpoint, or a hosted model with an explicit "your data will
be sent to this endpoint" confirmation, and a redaction boundary that every
outbound prompt passes through. **It is off by default, and this version's
interface exposes none of it**: there is no settings page and no button that
calls it. It is configured only by a file in the app directory (`ai.json`) and
reachable only through the local API. Nothing leaves your machine unless you
have done that by hand. Every AI feature is advisory: none of them changes the
deterministic analysis. When the interface for it ships, this page and
[What leaves your machine](install.md#what-leaves-your-machine) will change.

## Privacy and Terms

The **Privacy** and **Terms** pages inside the product carry a visible notice
that they have not yet been reviewed by counsel. They describe the product
accurately (local-first, no telemetry) and are drafts as legal documents. The
**Security** page (`/legal/security`) is the one to answer a client's
questionnaire from.
