# Golden v3 to CLI adapter contract audit (#2203)

Status: HOLD_PENDING_VALIDATOR

This additive audit freezes a pure mapping contract only. It does not modify
runtime or golden desktop code and performs no model, GUI, network, input, or
Docker execution.

## Frozen current-main sources

- `research/integration/golden_v3_result_schema_2186_v1/schema.json`
  `7fe3ad10ab69b0d8786d17ca854e65f90efd213b`
- `runtime/cli_v1/api.py`
  `5674bd39e3cb2170095f476dac90e2a781f4f77a`
- `runtime/cli_v1/receipt.py`
  `ebe71a2edfbb524a4288241686b969342a0bfcae`
- `runtime/cli_v1/README.md`
  `8cafa39718f0d5d66cb73adeb3aa99f0f1cce6d6`
- `runtime/golden_desktop_demo_v3.py`
  `26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2`

## Mapping matrix

| golden status/lifecycle | CLI boundary | disposition |
|---|---|---|
| doctor/setup | `doctor` diagnostic result | mapped, authority=false |
| model attempt/usage | result `usage` field | retained, no CLI execution claim |
| observation | receipt latest observation(s) | mapped as historical evidence |
| dispatch | `dispatch` request/result | mapped, admission remains required |
| refusal | `runtime_failed` or explicit refusal payload | fail closed unless typed reason retained |
| useful/partial effect | `result` plus `partial_effects` | retained; never inferred from process completion |
| stale invalidation/repair | status `stale_invalidated`, lifecycle `repair` | retained; no freshness renewal |
| release | lifecycle `release` | retained as evidence only |
| cleanup failure | `runtime_failed` + `cleanup_error` | non-success, original result/error retained |

The validator rejects authority escalation, unknown states, cleanup promotion,
missing partial-effects representation, and task/program conflation.
