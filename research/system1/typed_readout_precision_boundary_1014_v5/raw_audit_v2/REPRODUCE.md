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
```

Expected: `AUDIT_PASS_RAW_ONLY`, 27 rows, zero errors, five corruption controls rejected, and raw SHA-256 `c1a2256d8b117d7dc0ec7d90c7333f3356378313d7f735fb7aa7700278183624`. Any different raw bytes stop before parse or pass emission. This audit does not re-run the CUDA construction or alter its scientific interpretation.
