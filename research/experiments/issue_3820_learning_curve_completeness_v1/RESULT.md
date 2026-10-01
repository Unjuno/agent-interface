# Issue #3820 — learning-curve completeness audit

## H / T / D / C / U

- **H:** The merged #3807 formal bundle may include all secondary measurements requested by #3790, including held-out accuracy after each of 16 online feedback arrivals.
- **T:** Read the exact frozen #3807 runner and merged `FORMAL_RESULT.json`; inspect evaluation placement; verify per-seed timings and retained final-row evidence. Re-run the already-frozen independent result auditor in an isolated container. No training or prediction is performed.
- **D:** `PASS_MEASUREMENT_COMPLETENESS` only if both online arms retain 16 per-arrival accuracy values for all five seeds. Missing curves yield `HOLD_LEARNING_CURVE_NOT_RECORDED`, without changing the predecessor verdict.
- **C:** OrbStack Docker 29.4.0, Linux/arm64; pinned image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--network none`, read-only container root, read-only source mount, bounded tmpfs. Source/raw bytes are hash-pinned. No GPU/CPU model process, optimizer step, prediction, evaluation, data regeneration, or historical source modification.
- **U:** Measurement completeness only. Does not explain rank-4 collapse, validate a new training schedule, change final metrics, or establish LoRA/runtime/product benefit.

## Outcome

**`HOLD_LEARNING_CURVE_NOT_RECORDED`** for the secondary measurement-completeness gate.

The exact runner's `one_seed` function iterates through all 16 entries of `feedback_order`, invoking only the adapter update inside that loop. Its sole `eval_rows` call site is line 103, after the feedback loop and after all three arms have been trained. Consequently, held-out accuracy is evaluated only for the final model state; it is not measured after each arrival. The raw result confirms 16 update timings for each online arm per seed, final expected-label/prediction rows of 4096 for both arms, and no per-feedback accuracy curve.

| Seed | Rank-2 online updates timed | Rank-2 final accuracy | Rank-4 online updates timed | Rank-4 final accuracy |
|---:|---:|---:|---:|---:|
| 3451 | 16 | 0.94140625 | 16 | 0.01562500 |
| 3452 | 16 | 0.93261719 | 16 | 0.01489258 |
| 3453 | 16 | 0.93310547 | 16 | 0.02221680 |
| 3454 | 16 | 0.95825195 | 16 | 0.01342773 |
| 3455 | 16 | 0.93676758 | 16 | 0.01928711 |

The pre-existing independent auditor was run on the exact merged formal wrapper and still returns **`FAIL_ONLINE_RANK_CAPACITY_GPU`**, with integrity gates true. That scientific verdict is unchanged; this audit makes no causal inference about the low rank-4 final accuracies.

## Frozen input identity

- Main at audit start: `4c0765a23d62de7647109c2a524808a06e19c003`.
- #3819 merge commit containing the audited bundle: `dfd909eae5fdacdf699698f5f5e67b70e4395737` (ancestor of the main SHA above).
- `runner.py`: `43e6e6ef39883e78e50c3887b2ddf804a755f0305cad0d9ef6f640b00bdccdff`.
- `FORMAL_RESULT.json` (41,257 bytes): `abf9a01dd4dc34bc137bf4c25d191372ddceb8c872b3df73a61cdc9c30defc06`.
- Canonical decompressed raw result (333,120 bytes): `2ae484327db48fd1f428e2f724887edcdc06da771f0df97c5d2cfbda7a7d7bf0`.
- Existing independent `audit.py`: `d7f76504328a9492a8fe8f83be773e6b1a5a344e6da7cd0e4bd96192fec8bd7a`.
- This reproducible audit script: `1489a57ad4abcef9c6c9cd6edfdcda302dd23e1adf29edef25b7ee61b54a3e45`.

## Container verification

The committed `audit_learning_curve.py` was run once against the read-only checkout in the pinned OrbStack container. It checked all three frozen file hashes, decompressed and SHA-bound the raw result, parsed the runner AST to establish evaluation placement, independently recomputed final accuracy from retained expected/prediction rows, and invoked the frozen auditor to check the predecessor verdict.

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,size=64m \
  -v "$PWD":/src:ro -w /src \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python research/experiments/issue_3820_learning_curve_completeness_v1/audit_learning_curve.py \
  --runner research/needle_lora_3441_rank4_online_multiseed_gpu_v1/runner.py \
  --formal-result research/needle_lora_3441_rank4_online_multiseed_gpu_v1/FORMAL_RESULT.json \
  --auditor research/needle_lora_3441_rank4_online_multiseed_gpu_v1/audit.py
```

Container stdout is retained in `RESULT.json`. Initial harness construction attempts are retained here as well: the first inline invocation had a Python quoting/syntax error before audit code ran; the second stopped at an incorrect harness assertion expecting four `eval_rows` AST call sites rather than the actual single call inside a four-role loop. Neither attempt ran training/evaluation or altered evidence. The final committed harness was then run once and passed its frozen hash, raw integrity, row-count and verdict checks.

All prior #3807 raw, result, runner, audit, report, and manifests remain unchanged.
