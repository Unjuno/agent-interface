# Issue #6329 WSLc allocation-10

Fresh WSLc-native allocation to resume the bounded six-worker RTX 3080 memory-coexistence question. Allocation-09's Podman/crun pre-candidate STOP remains unchanged. See `PREREGISTRATION.md` and `FREEZE.json` before execution.

Current state: one separate CPU-only WSLc construction preflight passed; its raw receipt and independent recheck are in `construction-preflight-20261002-01/`. This does not satisfy the future in-window formal construction gate. No candidate, CUDA fit/workload, or formal auditor invocation has occurred. Resource request remains deferred/unassigned while another GPU need is pending. Formal candidate results must be retained under `formal-attempt-01/` only after a fresh exact assignment and current-main refreeze.
