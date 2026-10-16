# Distinguish unresolved effects from inconsistent checkpoint replies

The first prepared checkpoint caller wrote continuation-batch.json for any
needs_decision result whose reply status was boundary. The original policy used
needs_decision for both legitimate UNKNOWN evidence and malformed/mismatched
replies. A boundary reply with a wrong query identity or contract could therefore
produce a misleading continuation artifact, even though no finish was attempted.

checkpoint_finish_v2.py now defaults to needs_reconciliation with
continuation_allowed=false. Only an explicitly scoped, contiguous boundary with
the requested contract, open observation window, null task-success field and
no-authority metadata can return a continuable UNKNOWN. A correctly shaped busy
response is also continuable, with reason verifier_busy; it is not proof that the
effect failed or that any observation was refreshed. Timeout/batch-limit results
are checkpoint_pending without a continuation artifact. Other inconsistent
responses retain their transcript and require reconciliation.

prepared_checkpoint_v2.py consumes this explicit flag. It constructs a continuation
batch only when the policy permits it, and no longer tries to concatenate malformed
record fields on unresolved paths. There is no input replay, automatic retry,
lease renewal or default promotion. A continuable result still requires a new
explicit action decision and ordinary runtime admission.

| Reply condition | Result | Continuation file |
|---|---|---|
| Matching UNKNOWN evidence | needs_decision | yes |
| Matching busy response | needs_decision | yes |
| Timeout | checkpoint_pending | no |
| Wrong query/contract/cursor, gap, missing records, malformed busy, claimed task success | needs_reconciliation | no |

Thirteen policy controls continue to preserve positive/negative final evaluation
and no-finish precondition failures. The original synthetic busy control lacked
authority metadata; it is now rejected as malformed. A separate wrapper test uses
the recorded actual Calc program/checkpoint but mocks subprocess and socket I/O.
Ten cases verify the result state, explicit continuation flag, file presence,
retained record content on valid continuation, and exactly one checkpoint call
with no finish. This is not a new GUI run or a new assistant performance sample.

The change does not provide a universal schema validator, authenticated transport,
session restart identity or a general recovery policy. It relies on the existing
runtime event stream for well-formed prefix records. The archive, cancellation,
input and runtime implementations are unchanged. The v2 caller has not repeated
the full actual self-use flow; retain v1 and its frozen successful run as evidence
of that earlier implementation.

Evidence: probe_checkpoint_finish_controls_v2.py,
results/checkpoint-finish-controls-03, probe_prepared_checkpoint_continuation.py,
and results/prepared-checkpoint-continuation-01 with source and recorded-input hashes.
