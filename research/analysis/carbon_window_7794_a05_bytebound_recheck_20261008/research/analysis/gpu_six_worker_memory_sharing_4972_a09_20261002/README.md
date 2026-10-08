# Six-worker CUDA memory-sharing probe

Issue #6329 tests whether six independent processes can share bounded RTX 3080 memory in a WSL/Podman container. It is a functional coexistence probe only; it makes no GPU speedup or latency claim.

See PREREGISTRATION.md before any formal invocation. Freeze and source hashes are recorded in FREEZE.json and SHA256SUMS. Raw candidate and audit outputs are not checked in before a run.
