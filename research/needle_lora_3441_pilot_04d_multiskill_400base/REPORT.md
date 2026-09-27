# Issue #3912 — multi-skill LoRA, corrected 400-update base

## Disposition

`PASS_MULTI_SKILL_ROUTING_SCOPED` for one fresh-seed synthetic Windows host-GPU allocation. The base skill completed the preregistered **400** optimizer updates; B/C adapters each completed 120. This is not container evidence.

## Results

| Condition | A | B | C |
|---|---:|---:|---:|
| Explicit routed model | 0.970459 | 0.953613 | 0.936035 |
| Shared adapter, sequential B then C | 0.050293 | 0.000244 | 0.912598 |

All three routed held-out scores exceeded 0.90. The predeclared secondary interference contrast, mean routed B/C minus mean shared B/C, was **0.488403** (threshold 0.10). This supports the frozen synthetic multi-skill hypothesis for seed 3914 only.

The independent CPU auditor regenerated data/labels and recomputed all **24,576** retained row predictions with zero errors. Six invalid route controls returned YIELD. The base was tensor-identical; full module snapshots round-tripped and rollback checks passed. Adapter setup was 4.9229 ms; base pretraining 1058.7242 ms; adapter updates: shared-B 406.8761 ms, shared-C 338.6193 ms, separate-B 368.7621 ms, separate-C 165.7190 ms. Dispatcher-only median was 0.0001345 ms/call; this excludes model inference/loading. CUDA peak allocated memory was 69,009,408 bytes.

## Reproduction and retained evidence

The frozen runner, independent auditor, tests, preregistration and source identities are alongside this report. Exact formal stdout is losslessly retained as `FORMAL_STDOUT.json.gz.b64`; decompress the Base64-decoded gzip stream to reproduce the original 816,940 bytes. Its SHA-256 is `e932a3d3cd1c0796f10149a7b4805f4b1812547bf94c95fd1067f4f6a2fa516d`. Exact auditor stdout is also retained as `AUDIT.stdout.json.b64`. `AUDIT.json`, `FORMAL_METADATA.json` and `SHA256SUMS.txt` bind the audit and execution record.

The local GPU was an NVIDIA GeForce RTX 3080 Laptop GPU with Python 3.11.9, PyTorch 2.5.1+cu121 and CUDA 12.1. Deterministic algorithms were enabled, TF32 disabled, and `CUBLAS_WORKSPACE_CONFIG=:4096:8` set before process launch. Docker service/backend pipe were unavailable; execution was directly on this PC's host GPU. One formal invocation, zero retries, zero tuning.

## Evidence-transfer correction

After the formal run, GitHub blob readback showed that initial MCP staging calls had length-limited shell output and some uploaded files were incomplete. The original local frozen files and raw formal output were preserved. The exact preformal source files and byte-bound raw evidence were then re-uploaded; GitHub blob identities were checked against the full local contents. This storage correction did not edit or rerun the formal runner. See `FORMAL_METADATA.json`.

## Limits

One synthetic seed, one binary-factor task family and three closely related mappings. This does not establish realistic skill transfer, multi-user concurrency, crash-safe persistence, inference/model-load latency, GUI utility, production safety, runtime integration, or action authority. The independent auditor checks retained evidence; it does not reproduce training or independently regenerate the predictions from trained model weights.
