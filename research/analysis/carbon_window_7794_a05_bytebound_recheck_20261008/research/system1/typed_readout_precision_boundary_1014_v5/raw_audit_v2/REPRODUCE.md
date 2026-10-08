# Exact-byte raw audit v2

This additive successor addresses two audit-integrity findings on merged PR #4923 while preserving its v1 source and result. The runner checks the exact recovered raw SHA-256 before parsing, then validates the retained structure using explicit runtime checks (no `assert`). It never loads or calls a model.

Inputs are the unchanged sibling files in `../raw_recovery_v1/`: `raw_result.json` and `corpus.jsonl`. The runner reads model snapshot files only to verify their pinned hashes.

From this directory, run the fixture suite under each interpreter mode:

```sh
python -B -m unittest -v test_audit_v2.py
python -B -O -m unittest -v test_audit_v2.py
PYTHONOPTIMIZE=1 python -B -m unittest -v test_audit_v2.py
```

Then audit the exact recovery (set `MODEL_DIR` to the locally cached snapshot for revision `7ae557604adf67be50417f59c2c2f167def9a775`):

```sh
python -B audit_raw_v2.py --result ../raw_recovery_v1/raw_result.json --corpus ../raw_recovery_v1/corpus.jsonl --model "$MODEL_DIR" --out audit.json
python -B verify_audit_v2.py --result ../raw_recovery_v1/raw_result.json --corpus ../raw_recovery_v1/corpus.jsonl --weights "$MODEL_DIR/model.safetensors" --report audit.json
```

Expected: `AUDIT_PASS_RAW_ONLY`, 27 rows, zero errors, five corruption controls rejected, and raw SHA-256 `c1a2256d8b117d7dc0ec7d90c7333f3356378313d7f735fb7aa7700278183624`. The independent verifier rechecks raw/corpus/weight hashes and report invariants without importing the primary auditor. Any different raw bytes stop before parse or pass emission. This audit does not re-run the CUDA construction or alter its scientific interpretation.

## Frozen local Docker verification

The one-shot runner `container_launcher_v1.py` is frozen before execution. It stages only the four pinned audit sources, runs tests and audits under normal, `-O`, and `PYTHONOPTIMIZE=1`, then invokes the independent verifier under normal and `-O`. It does not load the model, perform inference, train, or request a GPU.

On Windows PowerShell, use the cached `python:3.11-slim` image by immutable image ID, with network disabled, read-only root, one CPU, 2 GiB memory, PID limit 64, read-only input/model mounts, and a fresh output mount. Do not pull the image or retry. The exact invocation and output hashes are recorded in the Issue #4939 execution comment and container receipt.
