# Progress-signature separation v1

Status: **RETAIN as next candidate; no ABI promotion.**

The current compiled runtime uses the same `evidence_digest` both as retained evidence identity and as its `no_progress` comparison. State-scoped presentation exposed that these two roles conflict.

## A — unrelated evidence changes are not semantic progress

Pre-action effect state: `a=False`; the pending effect requires `a=True`. `c` is unrelated. Six post states vary `a ∈ {False, True, unknown}` and nuisance `c ∈ {False, True}`.

Ground truth defines relevant progress only through `a`.

- full `a+c` digest comparison is wrong when only nuisance `c` changes;
- `a`-only effect progress signature matches **6/6**.

Thus a broad canonical evidence digest can produce false “progress” from irrelevant evidence changes.

## B — verifier dependencies matter when effect gate alone is insufficient

Second finite case: pending effect predicate `a=True` is already true, while the independent verifier depends on `b=True`. Six post states vary `a` / `b` including unknown.

- effect-only progress signature is incomplete;
- `effect ∪ verifier` signature matches **6/6**.

## Decision

Separate concepts:

1. **canonical evidence identity/provenance** — projection-independent retained evidence reference/digest;
2. **progress signature** — typed values needed to decide whether the pending effect/verifier received relevant new evidence.

Candidate progress dependency set is `pending expected-effect dependencies ∪ verifier dependencies`. This does not yet define the production ABI, and authorization/admission dependencies remain separate pre-action gates.
