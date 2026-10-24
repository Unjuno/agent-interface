# R17 result — usable screen observation and action passed, task oracle schema failed

## Disposition: HOLD_NOT_PASS

The same-session public `screen_physical_px` observation returned a nonblank image, was visually checked at the frozen gate, and bound the dispatch to target generation `6c8471d23316dfac526a53a0249470c0289b6744ab2124b19b24df8d9f321c7c`. Exactly one action was dispatched: call `b26e261c1cbf4a8e9bc981ee6be123f9`, operation `095235d667784d3f9cca602e02322179`. The independent UIA reads show 1,043 before and 1,044 after.

Dispatch reports completed input, `release_confirmed=true`, a verified empty release state, neutral completion readback bound to the same operation and generation, `replay_allowed=false`, and no unresolved calls after close.

`interface_verify_task` was invoked exactly once. Its configured UIA read found 1,044, but the runtime rejected the returned certificate as `independent_task_oracle_receipt_invalid: ... invalid schema`. The oracle returned 11 fields; the contract requires exactly seven: `call_id`, `operation_id`, `target_generation`, `oracle_id`, `outcome`, `observed_monotonic_ns`, and `evidence_ref`. Extra timing/UIA details caused the rejection. The one-use task-effect record is immutable; it was not retried. Runtime `task_success` therefore remains null even though separate UIA reads observed the expected result.

## Reproduction and next step

`audit_r17.py` validates the frozen manifest and reproduces the HOLD from retained dispatch, verifier, oracle, UIA and close receipts. The next distinct trial (R18) uses the same visible screen route and exact seven-field oracle certificate only; it begins from the current 1,044 state and targets 1,045. R17 is not replayed.

This does not establish MAP01, WSLc, bounded recovery, matched efficiency or reliability.
