# Issue #8668 T0 A03 — operation-bound stale acknowledgements

This is a new successor allocation for the exact review gap found in A02. A02's
one-shot source, raw output, and audit remain immutable. An independent review
found that A02 represented stale-ACK acceptance as a constant-false field and
mutated that field directly, so it did not test ACK identity through a decision
transition.

## Question and bounded hypothesis

For a non-idempotent logical action retried as a new operation, can a delayed or
reordered acknowledgement from the prior attempt falsely complete the active
attempt or authorize an unsafe duplicate retry? A strict controller should
accept only a monotone acknowledgement bound to the active operation ID and
attempt. A neutral input-release receipt is not semantic cancellation.

The finite plant varies the active operation phase, whether its effect
committed after emission, receipt arrival order/type, retry request, and neutral
release observation. It compares an operation-ID/attempt-bound policy with a
deliberately faulty identity-blind comparator. It also delivers both effect and
cancel acknowledgements for one active attempt in both orders; the controller
must preserve `CONFLICT_UNKNOWN`, while a late cancel acknowledgement after
emission alone remains `UNKNOWN`. This is a deterministic model only; it does
not test an OS, backend, GUI, application, model, or live task.

## Allocation and protocol

Allocation: `PHASE-CONTROL-DELAYS-8668-T0-A03-20261009`.

The source, schedule axes, oracle gate, and mutation controls are frozen in
`FREEZE.json` before the one formal candidate invocation. On candidate exit 0,
the independent raw-only auditor runs once. Preserve first outputs; no retries.
The previous A01 `FAIL_HARNESS` and A02 review HOLD remain separate evidence.

The result is not evidence that any real backend emits trustworthy operation
IDs or acknowledgements. A live transfer still needs separately authorized
allocation and observable backend receipts.
