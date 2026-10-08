# Golden desktop v3 → runtime.cli_v1 vertical-slice contract audit

Issue: #2172
Disposition: PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED

## Frozen source identities

| Source | Git blob |
|---|---|
| runtime/golden-demo-v3.sh | ef489bbd68e3f80fac060b179fe90da2cce8d209 |
| runtime/golden_desktop_demo_v3.py | 26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2 |
| runtime/golden_desktop_demo_v2.py | cf777186879fc3d550194aa9cbc8a7239ca991ff |
| runtime/cli_v1/api.py | 5674bd39e3cb2170095f476dac90e2a781f4f77a |
| runtime/core_v1/__init__.py | 659531954db218d4c04849fe937df80ad1fcf495 |
| runtime/selector_v1/__init__.py | 1a09fab9f2f67777decfe2373b0108f3a2609678 |

## Lifecycle mapping

| Golden lifecycle | CLI-compatible representation | Authority / loss check |
|---|---|---|
| setup / doctor | `api.doctor()` → schema, selection, runtime_available, side_effect_authority=false | diagnostic only; no authority |
| model attempt | dispatch result `status=returned` or `runtime_failed` | errors remain typed; no success inference |
| observation | `current_observation_seq` request field | invalid type/value rejected |
| guarded dispatch | `api.dispatch(program, targets, current_observation_seq, current_binding_revision)` | core/backend admission remains downstream |
| refusal / backend unavailable | `status=invalid_request` or `backend_unavailable` | no effect claim |
| useful effect | nested backend result only; golden independent scorer remains separate | program return is not task success |
| stale invalidation | `INVALID_OBSERVATION_SEQ`, `INVALID_BINDING_REVISION`, or backend result | no stale authority extension |
| repair | golden report's explicit repair record | must remain representable as partial effect, not collapsed to success |
| terminal release | backend close in `finally`; close failure changes status to `runtime_failed` | cleanup failure is non-success |
| cleanup failure | `status=runtime_failed`, `cleanup_error` | explicit failure, never hidden |

## Audit controls

- No mapping grants input authority; `doctor` explicitly reports `side_effect_authority=false`.
- `api.dispatch` validates observation and binding revisions before opening a session.
- Backend unavailability and runtime failure are distinct statuses.
- Session close is attempted in `finally`; close errors override success.
- Golden v3 `passed` requires independent evaluation, exact submissions, releases, repair record, call uniqueness and fixed turn count; program completion alone cannot satisfy it.
- Partial effects and failed calls remain serializable in nested result/task records.

## H/T/D/C/U

**H** — The existing golden lifecycle can be represented by the model-neutral CLI schemas without authority escalation or loss of failure/partial-effect information.

**T** — Frozen static source audit and independent field/mapping validator; no model, GUI, network, input or Docker invocation.

**D** — PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED because every required lifecycle state has a source-backed mapping, cleanup failure is non-success, and authority remains false.

**C** — This is integration-readiness evidence only. It does not implement an adapter or prove GUI correctness, latency, tokens, or end-to-end task completion.

**U** — Exact runtime adapter behavior and live golden demo reproducibility remain unverified; they require a fresh successor.
