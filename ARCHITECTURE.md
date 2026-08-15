# Architecture

Cleave is seven Python modules and one React application. The interesting part
is not the module list, it is that the boundaries between them are **mechanically
enforced**. A forbidden import does not get caught in review. It fails the build.

```
cleave/
  core/       schema, repository layer, domain events. SQLite per project, Alembic.
  ingest/     connectors + import pipeline. File import is connector #1.
  engine/     PURE analysis library. Dataframes in, findings out.
  report/     PDF / Excel / JSON / CSV export, plus IGA role export.
  web/        FastAPI on 127.0.0.1 + React SPA. The API-only boundary.
  ai/         optional, off-by-default AI layer (3 provider modes).
  generator/  synthetic-company generator. Built first, unblocks everything.
frontend/     React 19 + Vite + Tailwind v4. Builds into web's static mount.
```

## The four contracts

These live in `pyproject.toml` as [import-linter](https://import-linter.readthedocs.io/)
contracts and run in CI as `nox -s boundaries`. A second, source-level belt lives
in `tests/test_boundaries.py`, because a contract you can only read in config is
a contract nobody reads.

### 1. Layers: higher imports lower, never the reverse

```
cleave.web
cleave.report | cleave.ai
cleave.engine | cleave.ingest
cleave.core
```

`web` is the top and `core` is the floor. This is what makes v3's server
deployment a configuration change rather than a rewrite: the UI already talks to
the product only through `cleave.web`, so there is no hidden path from a React
component down into a repository.

### 2. Database access is confined to `cleave.core`

No module outside `core` may name `sqlalchemy` or `alembic`.

Note what is *absent* from this contract: an exemption for migrations. Alembic
revisions live inside `cleave/core/migrations/`, so they are covered by the rule
rather than carved out of it. A carve-out would have been a permanent hole in
the exact wall the contract exists to hold.

The contract is scoped to **direct** imports. Without that scoping it would
forbid the chain `ingest -> core.import_api -> sqlalchemy`, which is to say it
would forbid anything above `core` from using `core` at all, contradicting the
layers contract directly above it. The rule being expressed is "no module
outside `cleave.core` names a database library itself," and the direct-import
form is what says that.

### 3. The engine stays pure

`cleave.engine` may import the standard library and the scientific stack
(pandas, numpy, scikit-learn, networkx). That is the entire allowance. It may
not import `core`, `ingest`, `report`, `web`, `ai`, SQLAlchemy, Alembic,
FastAPI, Starlette, `requests`, or `httpx`.

This is the strictest boundary in the codebase, stricter than `ingest`'s, and it
had a real consequence during development. `ingest` had solved its own
persistence problem with a façade (`ImportGateway`) that it imports from `core`.
The engine cannot do that, because it may not import `core` at all. So
orchestration **inverts** instead: the engine exposes a pipeline callable that
the caller injects, and an AST-level test guards the arrangement.

The payoff is that the analysis library is a pure function of its inputs. It can
be tested with dataframes and no database, its determinism is checkable, and it
could be lifted out and run anywhere.

### 4. `core` does not depend on the generator

The synthetic generator is a development tool sitting outside the product
layering, not a runtime dependency. The bridge between the two lives in `tests/`,
so neither imports the other. This is why the generator
[extracts cleanly](synthgen/) into a
standalone MIT package: it was never entangled in the first place.

## Other structural seams

**Connector #1.** File import is not "the import code," it is the first
implementation behind a connector abstraction. Live connectors (AD/LDAP, Entra)
in v2 are additional implementations, not a refactor.

**The NHI seam.** Every identity carries a generic `type`
(`human` / `service` / `application` / `shared` / `unknown`) from the first
migration onward, even though v1 ships no non-human-identity features. Adding
NHI discovery later is a feature, not a schema migration across live customer
files.

**The redaction boundary.** The AI layer's outbound path accepts exactly one
type, `RedactedContext`, which has exactly one constructor guarded by a
module-private token. Code that tries to hand raw identifiers to a model fails
to type-check *and* fails at runtime. This is covered in detail in
[decisions/0004](decisions/0004-redaction-as-a-type-wall.md).

**`PRODUCT_NAME`.** The display name exists once, in `cleave/__init__.py`. A test
fails if it is hardcoded anywhere else, which keeps the product renameable.

## The job model

Every long-running operation (import, analysis, export) runs in a **spawned
worker subprocess** with a durable file store and an fsync'd NDJSON stage
journal. There is a FIFO queue with one global slot and per-project exclusivity
as the invariant.

The property that matters: the worker does its whole database write in a single
transaction, so **cancel is identical to an out-of-memory kill, which is
identical to a power cut**. All three roll back. This was verified by killing a
real worker mid-analysis and reopening the project, which came up clean with
prior runs intact rather than argued from first principles.

Startup reconciliation absorbs dead and orphaned workers. `result.json` is the
success marker, so a worker that dies *after* committing still reconciles
correctly from the database.

## The API seam

The server binds 127.0.0.1 only, validates the request host so another site in
your browser cannot reach it by re-pointing a hostname, and requires a
per-launch session token. The token rides the URL **fragment**, so it never
appears in a request line or a server log. There is no CORS configuration,
because there is no cross origin. The OpenAPI docs routes are behind the same
token.

`cleave/web/openapi.json` is **committed**, generated by `nox -s openapi`, and
freshness-tested from both sides. The frontend's TypeScript types are generated
from it by `openapi-typescript`. Nobody hand-writes an API type, and a route
change that skips the regeneration step fails CI.

## Determinism

Same data plus same parameters produces the same results. Randomness is seeded.
Analysis runs record their parameters, and results carry a fingerprint, so two
runs can be compared only when they are actually comparable. That last clause is
load-bearing and is the subject of
[decisions/0006](decisions/0006-comparability-as-a-precondition.md).

Imports are the only mutation path. Analysis never destroys data, and there are
no hard deletes anywhere in the product.
