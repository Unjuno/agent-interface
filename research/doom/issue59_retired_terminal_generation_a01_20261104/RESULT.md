# Owner-generation terminal handoff — A01 correction

## Correction

The original A01 note and PR #10212 incorrectly diagnosed a missing terminal owner-generation handoff in current main. The review stopped at `doom_process_identity_backend_v1.Backend._emit_identity` and `executor_v13` and missed the outer session emitter.

`session_map01_v12.main.emit` calls `InputOwnerGenerationProtocol.record_terminal(row, backend)` before writing events to `events.jsonl`, `delivered.jsonl`, and stdout. The v15 session imports v12 as `base` and replaces the backend and executor while retaining that emitter. `record_terminal` adds the backend's current `input_owner_generation` and `input_owner_id` to terminal rows. The existing `test_map01_process_identity_backend.py::test_cancelled_generation_rotates_owner_and_quarantines_late_reader` uses this protocol, passes the enriched terminal into `rotate_retired_owner_after_cancel`, then checks a fresh identity-bound observation and a new owner action.

Therefore the backend-level terminal annotation and synthetic stub-based regression added by PR #10212 duplicated existing session behavior. They did not establish a production defect or explain the historical r02 RuntimeError. Both redundant additions are removed by this correction.

## Historical r02 evidence boundary

The retained r02 trace still records a canceled `cover-1` terminal with empty X-server keymap, failed target-focus query, and a retired identity reader. Its next plan terminal is `needs_decision`, completed zero steps, with a verified empty X-server keymap, the reader retired, `interruption=null`, and `decision_reason=null`.

The preregistered commit is `26c383a983782be25d6a1ae33814f7c551d88d63`; its controller SHA-256 differs from current main. The retained failure receipt gives only `RuntimeError` at `active_action_execution`. The precise historical failure cause remains unknown. X-server keymap release does not establish physical Windows release or application consumption.

## Revalidation after correction

After removing the redundant production change, these current-main tests passed under Python 3.11.9 normally and under `-O`:

- `test_map01_process_identity_backend.py`: 7/7 each mode.
- `test_map01_overlap_controller_v39.py`: 24/24 each mode.
- `test_input_owner_generation_protocol_v1.py`: 6/6 each mode.
- `git diff --check`: passed.

The local `test_session_executor_factory_v1.py` import could not run because this Python environment does not have VizDoom installed. Its session integration remains represented by the source path above and the process-identity/protocol tests; no live game run was attempted.

## Decision and limits

Withdraw the A01 production-fix claim. The retained current-main tests cover the session protocol and owner-generation rotation in a synthetic/fake-X environment. This does not prove physical input release, live provider behavior, threat-policy effectiveness under MAP01, a MAP01 clear, or the exact cause of the historical r02 failure. Issue #59 remains open.
