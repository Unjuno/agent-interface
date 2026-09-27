# Static preflight FAIL02 — absent validation field

Distinct preformal `--read-only --network none` Docker container; no display or application was started and no GUI input was dispatched. All three `interface_validate` calls returned `static_valid=true`, `backend_checked=false`, and `runtime_admission=not_evaluated`. The response schema omits `input_dispatched` for validation, so the harness decoded it as `null`; preflight v1 incorrectly required an explicit `false` and returned `FAIL_STATIC_PUBLIC_MCP_VALIDATION`.

The exact first output is retained in the conversation/run log; the auditor/run source was not modified. This is a harness expectation FAIL, not a negative action result. Versioned preflight v2 accepts absent `input_dispatched` only alongside `backend_checked=false` and `runtime_admission=not_evaluated`, as specified by `interface_validate`'s read-only contract.
