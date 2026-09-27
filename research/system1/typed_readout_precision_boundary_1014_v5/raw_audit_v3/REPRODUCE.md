# Successor exact-byte audit v3 (Issue #4960)

This additive successor preserves #4939's one-shot STOP record. It normalizes wrapped GitHub base64 whitespace before strict decoding, then checks the exact byte length and SHA-256 of each embedded audit source before staging it read-only. The v2 audit implementation and scientific result are unchanged.

Host-only source decoder preflight:
```sh
python -B preflight_v1.py container_launcher_v1.py
```

The frozen local Docker invocation is recorded on Issue #4960. It uses the cached Python image by immutable ID, `--pull=never`, `--network none`, a read-only root, 1 CPU, 2 GiB, PID limit 64, a tmpfs scratch, read-only exact raw/corpus/model/runner mounts, and a fresh writable output directory. No GPU is requested. One formal invocation only; no retry.

The runner executes unit tests and the exact raw auditor under normal, optimized, and `PYTHONOPTIMIZE=1` modes, then runs the independent verifier in normal and optimized modes. PASS requires 27 rows, five corruption controls rejected, byte-identical 1,052-byte reports with the pinned SHA-256, and independent verifier success. Any mismatch records STOP/FAIL and preserves the receipt; it does not imply a scientific failure.

