# 0008. Cancel, out-of-memory, and power cut are the same event

**Status:** decided, shipped
**Area:** `web/`, `core/`

## The problem

Import and analysis are long operations over data a consultant cannot easily
re-obtain, running on a laptop that will be closed mid-run, run out of memory, or
lose power. During development, full-tier analysis runs were lost this way three
times, so this was not hypothetical.

The failure people actually fear is not the crash. It is the crash that leaves the
project file **half-written**: an import partly applied, an analysis run recorded
as complete with only some of its findings persisted. That file is worse than no
file, because it looks fine.

## The decision

Every long operation runs in a **spawned worker subprocess**, and the worker
performs its entire database write in a **single transaction**.

That one property collapses three failure modes into one:

- **Cancel** is `terminate()` on the worker.
- **Out of memory** is the OS terminating the worker.
- **Power cut** is everything terminating.

In all three cases the transaction never commits and SQLite rolls back. There is
no partial-write path to handle, because there is no partial write. Cancellation
needed no cleanup logic, no compensating transaction, and no "was this run
interrupted" repair pass, because it is not a distinct case.

## How it was verified

By killing a real worker mid-analysis and reopening the project.

The file came up clean with prior runs intact. This is stated as a measurement
rather than a design property on purpose: "the transaction rolls back" is what the
documentation says, and the interesting question is whether anything in the actual
code path had escaped the transaction.

## The supporting pieces

**A durable stage journal.** Progress is an fsync'd NDJSON file, appended
per-stage. The UI renders it as a real stepper showing which stages have completed,
rather than an invented percentage. Reloading the page re-attaches to the running
job.

**`result.json` is the success marker, not the process exit.** A worker that dies
*after* committing but before reporting is a real case, and it reconciles from the
database on startup rather than being declared failed.

**Startup reconciliation** absorbs dead and orphaned workers, so a machine that
lost power mid-run comes back to a coherent state without user action.

**FIFO queue, one global slot, per-project exclusivity as the invariant.** Two
analyses of the same project cannot interleave.

## The cost

It is a genuinely heavier architecture than running the work in a thread. It needs
process spawning, a file-based job store, journal plumbing, and reconciliation
logic, all before the first feature ships through it.

It bought two things worth the weight. Cancellation is free rather than a source
of subtle corruption bugs, and the API-only seam stays honest: the UI polls job
state over HTTP exactly as a future remote client would, so v3's server deployment
is a configuration change rather than a rewrite.

## The one thing it did not solve

Crash safety is not the same as **completing**. A full-tier run that rolls back
cleanly is still a run that did not finish, and the durable-commit checkpoint at
that scale exceeded 75 minutes before being killed. See
[0005](0005-nfr2-is-unmet-at-full-scale.md).

The job model guarantees you will not get a corrupt file. It does not guarantee
you will get an answer.
