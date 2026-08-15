# Decision records

Eight decisions from building Cleave, with the measurements that drove them.

These are drawn from the archived OpenSpec design documents, which recorded open
questions as open and resolved them with measurements taken afterward. Several of
those measurements refuted the design that proposed them, and those entries are
the ones worth reading.

| # | Decision | The short version |
|---|---|---|
| [0001](0001-reportlab-over-weasyprint.md) | ReportLab over WeasyPrint | A PDF library was rejected because its native stack sat outside the hashed lockfile, invisible to `pip-audit` and absent from the SBOM. Audit surface is a selection criterion. |
| [0002](0002-role-mining-defaults-to-clustering.md) | Role mining defaults to clustering | The intuitive grouping scored **F1 0.06**. The other scored **0.82**. It survived because the accuracy gate was quietly configured around the shipped default. |
| [0003](0003-retention-shipped-at-n2-not-n10.md) | Retention at N=2, not N=10 | The design assumed the findings tier was small. It is about one finding per access row, so N=10 would have been 164% of the project file. |
| [0004](0004-redaction-as-a-type-wall.md) | Redaction as a type wall | The AI provider interface accepts exactly one type, with one guarded constructor, so leaking identifiers fails to type-check. The wall held; the function inside it did not. |
| [0005](0005-nfr2-is-unmet-at-full-scale.md) | **NFR-2 is unmet at full scale** | A performance target the product currently fails, by how much, and which stage is actually binding. Peak 24.37 GB against a 16 GB budget. |
| [0006](0006-comparability-as-a-precondition.md) | Comparability is a precondition | A threshold change would have reported 85% of prior findings as *remediated*. Caught in security review before merge. |
| [0007](0007-the-threshold-was-the-fix.md) | The right defect for the wrong reason | The proposal's root cause was plausible, explained the symptom, and would have fixed nothing. Checking the score distribution took one query. |
| [0008](0008-crash-equivalence-in-the-job-model.md) | Cancel = OOM = power cut | One transaction per worker collapses three failure modes into one, so cancellation needs no cleanup path. Verified by killing a real worker. |

## A note on what is here

Four of these eight document something going wrong: a wrong default that shipped,
a design premise refuted by measurement, a misdiagnosed root cause, and a
performance target that is still missed.

That ratio is roughly honest for a real codebase. A decision log filled only with
correct calls made confidently on the first attempt is describing a project that
was never difficult, or is not describing the project accurately.
