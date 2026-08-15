# synthgen

**Deterministic synthetic identity and entitlement data, with ground truth, in
real vendor export formats.**

If you are building anything that analyzes access data (role mining, outlier
detection, separation-of-duties evaluation, access certification, an import
pipeline) you need test data. Real data you cannot share, and hand-made fixtures
have no hidden structure to find, so an algorithm that finds nothing looks
exactly like an algorithm that works.

`synthgen` generates a fake company from **hidden ground-truth roles plus
noise**, then writes it out in several vendor dialects along with a separate
ground-truth file. That means you can score your algorithm objectively:
precision, recall, F1, against roles you know are there because you planted them.

- **Zero dependencies.** The Python standard library and nothing else.
- **Deterministic.** Same `(seed, config)` gives byte-identical output, always.
- **Realistically messy.** Nested groups, non-UTF-8 files, tab delimiters,
  headers not on row 1, GUID group names, trailing total rows.
- **Ground truth never leaks** into the exports. Enforced by a test.

Built for [Cleave](../README.md), and built first, because no analysis algorithm
could be evaluated without labelled data to score against. **MIT licensed**
([LICENSE](LICENSE)) and independently usable: it does not depend on Cleave, and
you do not need Cleave to run it.

## Install

```bash
git clone https://github.com/SageHargrove/cleave
cd cleave/synthgen
pip install -e ".[dev]"
```

## Use it

```bash
# Print the shape of a company, write nothing
synthgen --tier small --seed 42 --summary-only

# Write vendor exports plus ground_truth.json
synthgen --tier small --seed 42 --out ./company

# Pick your dialects
synthgen --tier full --dialects sailpoint,entra --out ./big
```

```
tier=small seed=42
  identities   : 2,000
  applications : 20
  entitlements : 1,499
  roles        : 40
  assignments  : 43,087
  outliers     : 20
  sod          : 12
```

As a library:

```python
from synthgen import generate, preset, write_company

company = generate(preset("small"), seed=42)
manifest = write_company(company, "./out")
```

### Scale tiers

| Tier | Identities | Entitlements | Assignments |
|---|---|---|---|
| `tiny` | 40 | ~80 | ~350 |
| `small` | 2,000 | ~1,500 | ~43,000 |
| `full` | 50,000 | ~25,000 | ~3.8M |

The `full` tier generates and stream-counts in about two seconds. Assignments are
written one identity at a time and never fully materialized in memory, so the
large tier does not need a large machine.

## What comes out

```
out/
  sailpoint/  sailpoint_identities.csv  sailpoint_entitlements.csv  sailpoint_access.csv
  entra/      entra_users.csv (cp1252)  entra_groups.csv  entra_group_members.csv
  ad/         ad_users.csv (tab, preamble + total row)  ad_memberof.csv
  ground_truth.json
```

Each dialect describes the **same company** using that vendor's column names,
casing, delimiter, and multi-value conventions.

### The mess is the point

Every parser hazard here is one somebody actually hits in production:

- `;`-joined multi-value cells
- a Windows-1252 file sitting next to UTF-8 ones
- tab delimiters
- a header that is not on row 1, with a preamble above it
- a trailing "total" row that is not a record
- GUID group names carrying no human meaning
- two naming conventions in one estate, as though a subsidiary was acquired

If your importer survives all three dialects, it will probably survive a real
customer export.

## Ground truth

`ground_truth.json` is a single document with stable IDs so a scorer can join
predictions back to planted truth.

| Field | Meaning |
|---|---|
| `roles` | planted roles: `{id, archetype, department, entitlement_ids[], member_ids[]}` |
| `outliers` | `{identity_id, entitlement_id, reason}`, a rare-for-peers grant |
| `sod_violations` | `{id, rule, entitlement_a, entitlement_b, identity_ids[], via}` |
| `effective_paths` | access held **only transitively**, with the full group chain |
| `terminated_with_active` | identities terminated in HR but retaining active accounts |
| `orphan_account_ids` | accounts with no owning identity |
| `dormant_account_ids` | accounts with no recent login |
| `duplicate_account_ids` | second accounts for one identity on one app |
| `terminated_account_ids` | accounts belonging to terminated identities |

`effective_paths` is the one worth calling out. Those are grants a person holds
**only** by way of nested group membership, which is precisely the access that
naive tooling misses and auditors care about most.

Ground-truth labels never appear in any export file. `groundtruth.find_leaks`
enforces this and it is covered by a test, because a label that leaks into the
data turns your benchmark into a lookup.

## Scoring

```python
from synthgen import scoring

truth = scoring.outlier_truth(company)
score = scoring.prf(my_predicted_outliers, truth)
print(score.as_dict())    # {'precision': ..., 'recall': ..., 'f_score': ...}
```

Projections provided: `outlier_truth`, `sod_truth`, `role_membership_truth`.

### This is not a toy benchmark

In the project this came from, scoring against these labels showed that the
intuitive role-mining approach (group people by department and title, find the
shared bundle) scores **F1 0.06**, while clustering peer groups scores **0.82**.
A department contains several roles, so attribute grouping can only ever recover
one of them.

That defect was invisible in a UI. The candidate roles looked perfectly
plausible. It took ground truth to see it. The
[full writeup is here](../decisions/0002-role-mining-defaults-to-clustering.md).

## Known limitation

**Outlier precision is not currently measurable.** Unlabeled over-provisioning
noise is drawn from the same entitlement pool as the labeled outliers, at a
measured ratio of about 1:60, which makes the two statistically identical by
construction. Recall and rank quality score fine. Precision does not mean
anything yet.

Drawing noise from role-reachable entitlements instead would fix this. It is a
known open issue rather than a subtlety waiting to embarrass you, which is why
it is in the README.

## Development

```bash
pip install -e ".[dev]"
pytest          # 25 tests
ruff check .
mypy synthgen
```

## License

MIT. See [LICENSE](LICENSE).
