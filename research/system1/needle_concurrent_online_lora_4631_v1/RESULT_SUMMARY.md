# Issue #4631 — concurrent Needle online-LoRA/System-1 inference

**Disposition: `STOP_AUDIT_IMPLEMENTATION_BUG_AFTER_TRAINING`.** The sole frozen Docker orchestration ran once. The trainer exited 0 and produced all nine seed/arm raw files, but the independent auditor's output is unusable: frozen `audit.py` passes a one-dimensional query vector into `F.linear` and returns `[0]`, a scalar, then compares that scalar with the runner's four-logit vector. This creates 1,079 `proposal_recompute` / `stable_live_recompute` errors across rows even for the inference-only baseline. Source review explains the failure; no second auditor, training run, correction, or retry was performed. Do not interpret the auditor's program label `FAIL_VERSION_INTEGRITY` as a measured model/version-integrity failure.

## Execution record

- Frozen allocation: `needle-concurrent-online-lora-4631-v1`, source freeze SHA-256 `9f6fc9e20776fd3ba33c7a240f45b9fd3a08e17c13ada1045445e2965de676ea`.
- Base main at allocation freeze: `6081879249170a41cd4467cbbe47b18012d71d41`; branch `research/needle-concurrent-online-lora-4631-v1-20260927`; only this allocation's additive path is intended.
- One host invocation: `py -3.11 formal.py --source <source> --out <out>`. The operator intended construction-only but omitted `--construction-only`; the frozen wrapper therefore ran the one formal allocation after its construction suite. The source and test were already frozen. No further formal invocation is allowed.
- Construction suite: 7/7 passed in the pinned image before the trainer container started. No optimizer was constructed by the tests.
- Docker 29.8.0; cached image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; Linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, CPU-only, one intra/inter-op thread, network none, read-only source/root, 1 CPU / 2 GiB / 64 PIDs. Optional NumPy initialization warning only; no install.
- Trainer exit 0; all 9 cells retained, 120 queries per seed/arm, 192 AdamW adapter steps in each trained arm per seed, no worker errors, no actions/effects. Auditor exit 2; its retained output has 1,079 comparison errors. Retry count: 0.
- The host output folder was named `preformal_construction` by the operator; despite that misleading name, it contains the complete formal invocation, trainer/auditor logs, raw data and audit output. Preserve the folder and logs byte-for-byte.

## Raw timing / overlap diagnostics (not an audited result)

The frozen auditor did parse and emit timing/overlap summaries, but its correctness recomputation gate failed globally. These figures are retained only as raw-run diagnostics, not an independently validated real-time claim.

| Seed | COW query intervals overlapping updates / 120 | COW inference p95 (ms) | COW 60 Hz deadline misses |
|---:|---:|---:|---:|
| 88117 | 4 | 0.695583 | 1 |
| 88229 | 4 | 0.601055 | 0 |
| 88301 | 21 | 0.976107 | 0 |

Thus two seeds fell below the preregistered minimum of eight overlapping queries, and one COW seed missed a deadline. Because the auditor is invalid, no COW version-integrity, quality, or scoped-PASS conclusion is certified. These diagnostics do not justify a post-result extension.

## Scope and next work

This is a harness STOP after training, not a scientific LoRA-quality result. Preserve the frozen source, raw JSON, and `AUDIT.json` exactly. Any further work requires a new successor allocation with an independently reviewed vector-shape-correct auditor and a fresh preregistration; it may not rerun this consumed allocation or rewrite this outcome. No Astra feedback, GUI/task effects, large-model contention, action authority, or runtime promotion was tested.
