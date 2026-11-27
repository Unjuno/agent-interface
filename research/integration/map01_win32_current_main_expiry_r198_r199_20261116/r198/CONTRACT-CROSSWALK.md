# R198 current-main status contract crosswalk

Read-only audit against the R198-frozen current-main source (`86a52662dc2bb690dd670d52ea8d97816aef2a26`). No runtime files were changed.

| Evidence | Current-main contract | Relevance to R198 |
|---|---|---|
| `runtime/cli_v1/owned_win32_session.py:1627-1649` | The source action is marked `recovered` only when cancellation operation ID and target generation match, cancellation/result phase and status are `recovered`, and release confirmation is true. Task success remains null. | R198's action status `recovered`, release true, `task_success=null` matches this branch. |
| `runtime/cli_v1/owned_win32_session.py:1652-1670` | For the standard-program branch, a confirmed recovery maps to `recovered`; otherwise the status maps to `unknown`. The result carries `effect_status=unknown` and `task_success=null`. | Recovery state is not equivalent to task success. |
| `runtime/cli_v1/test_supervised_win32_compiled.py:516-530` | The composed-path test explicitly selects source status `recovered` when `automatic_unknown_source` is false and `unknown` when true; the `recovered` source has release true, while `unknown` has release false. | This is the exact semantic split R198's frozen query projection failed to reflect. The suite had already passed in the recorded current-main normal and `-O` runs. |

## Adjudication

R198's frozen `protocol.query_projection` expected source action `unknown` and release false, while current main returned `recovered` and release true with the joined operation/generation/release proof. The data supports the runtime's confirmed-recovery branch. Therefore the protocol mismatch is a stale experiment expectation, not evidence of a runtime defect. Keep the raw runner label, but classify R198 as a partial positive effect observation with a frozen-condition deviation; do not retroactively rewrite the conditions or count it as a full preregistered pass.

A future distinct attempt must freeze the expected projection from the current-main contract and still require `task_success=null` unless a separate semantic success criterion is verified. R198 must not be replayed.
