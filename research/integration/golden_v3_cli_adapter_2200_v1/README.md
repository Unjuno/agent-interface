# Golden v3 to CLI adapter contract audit (#2203)

## Disposition

HOLD_ADAPTER_CONTRACT_NOT_SOURCE_BACKED

This is a read-only research validator, not a production adapter. It pins current-main source blobs and compares the proposed golden-v3-result-v1 fields with actual CLI/API source. The CLI emits returned, backend_unavailable, and runtime_failed; the proposal requires success, partial, refused, stale_invalidated, and cleanup_failed. No unverified mapping is inferred.

Unverified fields remain program_completed, task_success, status, and partial_effects. cleanup_error is CLI-source-backed; lifecycle and usage are documented-only. authority_granted=false is a derived guard, not an effect receipt.

The finite audit accepts internally consistent contract-shaped records and rejects authority=true, unknown CLI status, missing partial effects, and success/task contradictions. It calls no runtime, model, GUI, network, or input.

## H/T/D/C/U

- H: A pure adapter contract audit exposes every schema/CLI mismatch while preserving authority and refusing unverified task/effect claims.
- T: Run once in python:3.12-slim; require exact source SHA manifest, status-set comparison, three accepted controls, four rejected controls, zero authority grants, and HOLD when required fields are unverified.
- D: standard-library-only deterministic fixtures and independent shell assertion over JSON.
- C: No schema status is promoted into a live CLI meaning. Cleanup failure remains fail-closed.
- U: No production adapter, model utility, GUI correctness, task success, latency, or desktop readiness claim.
