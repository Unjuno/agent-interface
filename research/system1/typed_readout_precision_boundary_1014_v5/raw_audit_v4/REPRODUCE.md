# Canonical-LF exact-byte raw audit (Issue #4963)

This additive successor preserves #4939 and #4960 STOP evidence. It validates the baseline report's exact 1,052-byte CRLF SHA-256, canonicalizes only CRLF to LF, verifies the canonical 1,017-byte SHA-256, and requires every generated report to match those canonical bytes exactly. All four auditor/test/verifier sources are independently pinned and staged read-only after wrapped-base64 whitespace normalization.

The host-only decoder/baseline preflight is:
```sh
python -B preflight_v1.py container_launcher_v1.py
```

The single formal PowerShell/Docker invocation is frozen in Issue #4963 before execution. Local cached image by ID only, no pull, no network, read-only root, 1 CPU, 2 GiB memory, 64 PID limit, tmpfs scratch, read-only exact inputs, and a fresh output directory. GPU/model-load/inference/training are forbidden. No retry.

Success requires normal, `-O`, and `PYTHONOPTIMIZE=1` unit tests and audit runs, normal and `-O` independent verifier passes, 27 validated rows, five corruption controls rejected, and byte-identical canonical reports across modes. Any mismatch yields a preserved STOP/FAIL receipt.
