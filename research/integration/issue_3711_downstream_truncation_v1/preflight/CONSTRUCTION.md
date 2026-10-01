# Source-import construction checks (not formal allocations)

These checks only imported the frozen CLI module in an isolated container; none called dispatch, observe, or input backends.

1. **STOP_SOURCE_CLOSURE_01:** pinned Python 3.12 linux/arm64 image, network disabled, source/root read-only. Import stopped with `ModuleNotFoundError: runtime.selector_v1` because the sparse checkout contained only `runtime/cli_v1/**`.
2. **STOP_SOURCE_CLOSURE_02:** after adding `runtime/selector_v1/**`, import stopped with `ModuleNotFoundError: runtime.motor_state_v1` from the CLI receipt module.
3. **PASS_SOURCE_IMPORT_PREFLIGHT_03:** statically followed top-level imports and added `runtime/motor_state_v1/**`; the same bounded import-only command completed with `SOURCE_IMPORT_PREFLIGHT=PASS` (exit 0). This verifies import closure only; it is not downstream-truncation evidence.

Both preflight failures are preserved as construction failures. Neither is allocation-01's formal STOP, and neither is a CLI behavior result. Formal successor allocation 02 freezes the expanded source closure and will run once only after its own H/T/D/C/U and hashes are posted to Issue #3711.
