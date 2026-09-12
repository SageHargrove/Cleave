# Reports and exports

After this page you can produce every export Cleave makes and know what each one is for.

**Reports** in a project's sidebar makes all of them. Four export formats
(`pdf`, `xlsx`, `json`, `roles`) run as background jobs and appear in the list
below with a download button; every table view is also available directly as
CSV. All of them come from the same run, and all of them carry the same
methodology block, so they cannot disagree with each other.

Producing an export needs a licence on a regular project; the sample project
is exempt ([Exports and the licence](#exports-and-the-licence)).

## Excel

`xlsx`: the working file. One sheet per view (outliers, SoD violations,
hygiene, candidate roles, peer groups, the access matrix), each with a frozen
header row and an auto-filter over the whole used range, plus a **Methodology**
sheet ([The methodology block](#the-methodology-block)). This is what you open
to sort, filter, pivot and shape candidate roles before they go anywhere.

The access matrix is one row per account-entitlement pair of effective access,
which on a large estate exceeds what a worksheet can hold. When it does, the
sheet stops at the worksheet's row limit and says so in its last row
(`[TRUNCATED]`, with the count), and the whole matrix is available as CSV or
JSON instead. The other sheets are never truncated.

## PDF

`pdf`: the executive report, for the person who will not open a workbook. Fill
in the cover: **Client name**, **Subtitle** ("Access review, Q3"), **Prepared
by** (your consultancy), and optionally a **Cover logo** (PNG or JPEG,
uploaded and kept with the project). If you leave the logo out there is no
empty box where it would have been. A small Cleave mark sits below your
branding, subordinate to it.

The story: cover, summary, findings, candidate roles, methodology. The findings
section describes the population before it shows rows (how many findings, how
many peer groups, how concentrated), then shows one finding per peer group
rather than the top of a score-sorted list, for the reason on
[Peer-group size](findings.md#peer-group-size). Scores print to three decimals.
The methodology appendix is the last thing in the document, so a reader who
doubts a number can find, on the last page, exactly which parameters produced
it and what the run warned about.

Rendering the sample's report took 0.2 s (measured 2026-08-17); a large estate
takes longer mostly because the findings section has more population to
describe, and the report is a job like any other.

## JSON

`json`: everything, machine-readable: findings with their full why payloads,
candidate roles, peer groups, warnings, and the methodology as a key. This is
what to hand to someone who wants to load the results into their own tooling,
and it is the complete form of the run; the PDF and the workbook are views of
it.

## CSV

Each table view can be downloaded as a CSV file straight from the Reports
page, from the view itself (the Outliers view has its own download button), or
from the Explorer. The views are:

| View | Rows |
| --- | --- |
| `outliers` | one per outlier finding, with score, rarity, weight and the why summary |
| `sod` | one per separation-of-duties violation |
| `hygiene` | one per hygiene finding, with the issue type |
| `candidate_roles` | one per candidate, with members, coverage, cost, parent |
| `peer_groups` | one per peer group, with method and size |
| `access_matrix` | one per effective account-entitlement pair, with whether it is direct and the path if not |

CSV streams as it is produced (no job, no waiting for a large view to
materialise), and the methodology block rides at the top as lines beginning
with `#`, so the file still opens as a plain table in Excel and still says
where it came from. Values that a spreadsheet would read as a formula are
neutralised on the way out.

## The methodology block

One block, rendered four ways: the PDF appendix, the Excel Methodology sheet,
the `#` preamble of every CSV, and a key in the JSON. It states the run's id
and time, the estate numbers, the **full parameter set** that produced the run
(not only the six the panel shows), the peer-grouping method actually used,
every warning the run raised, unfiltered ([Warnings](analysis.md#warnings)),
and, on the sample project, that the data is synthetic. It is generated from
one place, so the four cannot drift, and it is what makes a report reproducible
from the project file it came from.

Read it before you present. If a check did not run (dormancy without last-login
data is the common one), it says so there, and so should you.

## IGA role export

`roles`: candidate roles in a form an IGA suite can import, so a mined role
can become a defined one without retyping. On the **Role mining** view, select
candidates and choose **Export as role model…**; pick a format:

- `sailpoint-iiq`: an XML document of `<Bundle>` elements for
  `iiq console import`. IIQ uses the bundle name as its unique key, so two
  candidates with the same name would collide on import; check names before
  importing ([Limits](limits.md#iiq-bundle-names)).
- `generic-json`: the same candidates as plain JSON, for anything else.

What is exported is the candidate as mined: its name, its members and its
entitlement bundle. Refinement happens before or after, outside the tool
([Candidate roles](findings.md#candidate-roles)).

## The synthetic mark

Every export from the sample project states that the data is synthetic: on the
PDF cover and in its methodology, on the Excel Methodology sheet, in the CSV
preamble and in the JSON. The statement comes from a fact about the project
that was set when `cleave-sample` created it, so renaming the project does not
remove it, and no export from a regular project ever carries it. Using the
sample's own client name on the cover (`Northwind Traders (synthetic sample)`)
is a courtesy, not the mechanism.

## Where exports go

Under the app directory ([Where things live](install.md#where-things-live)),
in `exports/<project id>/`, and they stay there until you delete them. The
Reports page's list is the history of what was produced, with a download for
each. An export produced while licensed remains downloadable after a licence
lapses; only *producing* new ones is refused.

## Exports and the licence

On a regular project, generating any of the four formats or downloading a table
CSV needs a current licence; without one the buttons are disabled with the
reason and a link to the Licence page, and the server refuses if asked anyway
([What read-only means](licence.md#what-read-only-means)). The sample project
exports freely.
