# Exact raw-result recovery — Issue #4912 v5

This is a publication-only recovery for the one-shot CUDA construction already recorded by #4912 / PR #4919. It does not modify that original branch/result, rerun inference, change a decision gate, or consume a seed.

The merged/draft result bundle retained only an aggregate `result.json`; the raw-only audit refers to a distinct per-row file with SHA-256 `c1a2256d8b117d7dc0ec7d90c7333f3356378313d7f735fb7aa7700278183624`. The exact pre-audit 12,160-byte file was recovered from the existing local construction output and copied unchanged to `raw_result.json`.

A separate CPU-only invocation of the published `audit_raw.py` / `audit_core.py` over those exact bytes returned `AUDIT_PASS_RAW_ONLY`: 27 rows, zero errors, 5/5 corruption controls rejected, and corpus/model-weight hashes match the freeze. The auditor validated retained raw values and did not load or call the model. Python 3.11.9; no GPU and no Docker container were used for this publication audit. No optimizer steps, inference, generation, training, retries, or tuning occurred.

## Scope

The recovery makes the existing raw audit reproducible from the repository. It does not extend the nine-pair synthetic precision construction, establish speed or task-quality gains, or change the scoped result: FP32 passes both tolerances on 9/9 pairs; FP16 and BF16 pass 0/9. The original v4 STOP and v5 one-shot remain immutable.
