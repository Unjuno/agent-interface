# Recovered raw Ollama server log

This is an exact-byte recovery of the temporary server log referenced by the exploratory GPU smoke report in this directory.

- Recovered from the existing Arch WSL file `/tmp/ollama-gpu-smoke-20261003.log` on 2026-10-03 JST; no model inference was rerun.
- Original and recovered byte count: 31,264.
- SHA-256: `e402d703e5f95a88b1dd2f3e5bd2e28d394fc6fcb12131056471615da468b5c0`, matching the checksum already reported in `REPORT.md`.
- The raw log is preserved unchanged as `ollama-gpu-smoke-20261003.log`. It contains expected local model-store mount paths but no credential-like pattern was detected in the reviewed bytes.
- This supplements auditability only; the original response-contract FAIL, GPU-route PASS, one-shot count, and claim limits are unchanged.
