# Bind event boundaries to explicit action identity

Private EventCursor v2 accepts optional action_id. Requested event names use an
explicit identity mapping: accepted/terminal/observation/cancel_requested use id;
effect_evidence/independent_evaluation use final_program. Embedded effect.action_id
must agree when present (required for effect_evidence). No field guessing or
semantic attribution is introduced. Socket v7 exposes --action-id and rejects
a submit/cancel whose command ID differs from its requested action scope before
writing. Unscoped reads preserve their previous behavior.

Other action records remain in the returned prefix; they cannot satisfy a scoped
boundary. Missing identity gives identity_unknown, inconsistent identity gives
identity_conflict. Current runtime rejected records lack action identity, so a
scoped read returns unattributed_rejection promptly, even if rejected was not one
of the requested boundaries. This exposes uncertainty rather than discarding the
notification or claiming it belongs to the requested action. Unsupported scoped
event kinds fail validation before dispatch.

## Evidence

Replay of the frozen actual-assistant Calc stream demonstrates the original
unscoped read stops at enter_save's terminal. A read scoped to confirm_excel
returns all 23 preceding records through that terminal, then a separate read
matches its effect at cursor 24. Controls preserve other-action records without
matching, and explicitly return missing/conflicting identity and unattributed
rejection. Results and listed source hashes: results/event-scope-01.

The live socket-action-scope-01 xterm probe uses scoped submit/cancel/terminal
reads while another observation request waits. Cancel response is 48.565 ms;
terminal is cancelled with verified release, and the disconnected clock retry
is not duplicated. Two exact public AIT/PNG frames, source hashes and owner close
are audited by audit_socket_action_scope.py. This live run exercises the new
socket fields; the wrong-action counterexample is retained-event replay, not a
live competing-action race.

## Limits and next boundary

This is optional and not a new input authorization. Identity is event metadata,
not authenticated causal proof. No session incarnation, restart-safe cursor or
runtime-owned rejection request ID is added. A metadata error for another event
can conservatively interrupt a scoped wait. Pending events still obey bounded
retention/gap semantics; receiving them does not acknowledge resolution. Tests do
not establish general planner speedup, actual model tokens or cross-domain gains.

Next give rejections explicit request correlation at the runtime boundary and
test stale observation, expired lease and malformed program against concurrent
readers. Do not infer rejection ownership from timing or the currently active
program. Keep unscoped uncertainty visible until correlation is demonstrated.
No default promotion or freeze credit.
