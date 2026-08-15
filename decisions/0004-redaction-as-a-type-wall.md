# 0004. The AI redaction boundary is a type wall, not a code review rule

**Status:** decided, shipped
**Area:** `ai/`

## The problem

Cleave's AI layer is optional, off by default, and useful: it can name a cluster
of entitlements, suggest a column mapping for a messy export, or write a
plain-English explanation of a finding.

Every one of those features wants to send something to a model. Cleave holds
enterprise identity data. So each feature is an opportunity for someone's
distinguished name, email address, or directory identifier to leave the machine.

The normal way to handle this is a `redact()` function plus a rule that everyone
calls it. That rule holds right up until the first feature written in a hurry, and
its failure is silent: nothing breaks, tests still pass, and identifiers ship.

## The decision

Make the guarantee structural.

`RedactedContext` is the only type the provider interface accepts.
`Provider.complete` takes `RedactedContext` and nothing else. `RedactedContext`
has exactly **one** constructor, `redact()`, guarded by a module-private token, so
it cannot be constructed from outside the redaction module even by accident.

The result is that a feature attempting to hand raw identifiers to a model **fails
to type-check, and also fails at runtime**. Leakage is not prevented by
discipline. It is prevented by construction.

## What goes out

- Holder populations become job-title and department **distributions** rather than
  rosters.
- Mapping assistance sends at most five **masked** sample rows, shape hints only.
- Finding explanations are built from the `why` payload with identifiers scrubbed.
- The local prompt and response log records exactly the post-redaction payload,
  never a key.

Hosted egress additionally requires an explicit "data will be sent to
`<endpoint>`" confirmation, and choosing a provider endpoint outside your own
network is a separate consent step.

## What the review caught anyway

The type wall held. The redaction *function inside it* did not.

Security review found that `redact()` was trusting **key names** rather than
inspecting values. It was, in effect, a provenance stamp. An email address under
an unlisted key, or nested inside a list, egressed raw, and free-text enrichment
fields were never scrubbed at all. The `local` provider mode also accepted any
internet URL with no consent step, so "local" was a label rather than a
constraint.

This is worth recording because it cuts against the decision's own story. The
wall guaranteed that everything outbound passes **through** one function. It could
not guarantee that the function was correct. Those are different properties, and
the first is still worth having: there was exactly one place to fix, and fixing it
fixed every feature at once.

The retuned matcher then over-corrected and stopped masking `userName`, `logins`,
and `accounts`. Self-review caught that in the same sweep and pinned it with
tests.

## Supporting decisions

**`cleave.ai` is database-free.** Persistence rides an `AiGateway` in `core`,
following the existing gateway pattern, so the layering and database-confinement
contracts hold unchanged and `core` still imports no `ai`.

**Secrets never touch the project file.** API keys live in the OS keychain with an
environment-variable fallback, configuration lives in a per-user file. A project
file handed to a client leaks neither your keys nor another client's data, and a
test asserts the AI tables have no key or endpoint columns.

**Features run synchronously per item, not as background jobs.** This was a change
from the design, made during implementation: the job model would have carried the
API key across into a worker subprocess. Running synchronously keeps the secret in
one process. Outputs are short enough that it costs nothing.

**AI is advisory only.** Enrichment and explanations never feed the engine and are
excluded from fingerprints. A determinism test proves findings, scores, and
fingerprints are byte-identical with AI on and off.
