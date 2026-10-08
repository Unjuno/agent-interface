# Planner evidence binding and partial-evidence pilot

`planner_evidence_v4.py` is the current opt-in extension for the bounded effect
wait path. It preserves caller request/contract binding and explicitly records
whether a validated program came from durable journal v4, v5 or v6. Three known
revisions pass; two unknown revisions plus three malformed/binding cases refuse
before model or GUI work. The first live v6 attempt using v3 is retained because
v3 correctly rejected the new journal revision. See `PARTIAL_TERMINAL_WAIT.md`.

`planner_evidence_v2` validates a checkpoint against the contract carried by
that checkpoint. It did not itself require the caller to state the request ID
and completion contract expected at the current decision boundary. The durable
caller checked those values elsewhere, but a planner presenter should fail
before model delivery if a valid checkpoint belongs to another query or task.

`planner_evidence_v3.py` adds two mandatory caller inputs:

- `expected_request_id`
- `expected_contract`

It first runs all v2 validation, then requires exact request identity and a
canonical contract match. Its output retains the v2 view and adds an explicit
binding block stating that the match was verified before presentation. This is
a presentation boundary only. It grants no input authority, permits no retry
and does not turn program completion into application success.

The archived controls use four real prior states: form UNKNOWN, form VERIFIED,
Calc UNKNOWN after a partially submitted Save sequence, and Calc VERIFIED. All
four preserve the previous v2 view except for the new binding block. Nine
adversarial cases are refused before any model call or action: wrong, empty or
oversized expected request IDs; different form value; different contract kind;
missing or unsupported expected contracts; disagreement between record and
resolution identity; and a missing record contract. The independent replay
audit passes. Artifacts: `results/planner-evidence-controls-03/`.

This follows the same boundary as idempotency-key protocols: an operation key
must not be reused for a different payload, and a client facing an uncertain
non-idempotent result must not assume that blindly repeating it is safe. The
[IETF HTTPAPI Idempotency-Key document](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header)
is an expired Internet-Draft rather than a final standard, so it is design input
rather than normative authority here.
Agent Interface additionally binds application-effect contracts because replay
identity alone cannot prove that a GUI side effect occurred.

## Confounded model pilot retained

`partial-evidence-decisions-01` attempted to compare the strict v3 partial
program view against a lossy view with `execution`, `prior_steps` and `binding`
removed. The same Calc dialog image and task prompt were used for eight calls.
All four strict and four lossy calls proposed one dialog click, with zero Save
repeats. No action executed.

That result does **not** show that the removed fields are unnecessary. The
common replay prefix explicitly said that a prior Save may already have been
attempted. It therefore reintroduced the omitted action-history fact into both
conditions. The pilot, calls, tokens and audit are retained, but the comparison
is frozen as confounded and supports no compression or reliability claim.

[The corrected delayed-effect comparison](DELAYED_EFFECT_DECISION.md) now uses
an actual Chromium submission whose saved effect arrives five seconds later
without changing the page. With the same screenshot and common prompt, all four
strict calls wait/check and all four checkpoint-only calls submit once. This
shows that execution history is decision-relevant in that declared state and
cannot be removed as lossless compression. Redacted-observation semantics remain
a separate experiment: hidden pixels must actually be withheld, explicitly
marked UNKNOWN, and checked for alternate-channel leakage before evaluation.

Primary related issues are #34 (verified effects), #38 (redacted observations)
and #39 (typed negative outcomes).
