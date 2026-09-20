# Per-skill LoRA routing — Issue #3701

Successor to #3441 pilots 01–03. This is a synthetic component experiment only; earlier results are preserved unchanged.

## Observed metrics and disposition

The single Windows-host RTX 3080 Laptop GPU run (PyTorch 2.5.1+cu121, CUDA 12.1) observed the metrics below; Docker Desktop was unavailable, so this is not a container result. The formal disposition is **HOLD_PROTOCOL_DEVIATION**, not PASS: a pre-allocation Issue #3701 clarification required tensor-by-tensor equality for every full module state_dict tensor, but the frozen snapshot saved only trainable adapter tensors `a`/`b` (the shared base was checked separately for immutability). Adapter setup time was also not isolated, and a parallel same-issue branch recorded a separate pre-update CUBLAS STOP. Details are in [DISPOSITION_AMENDMENT.md](DISPOSITION_AMENDMENT.md).

| Held-out skill | Explicit per-skill route | One shared adapter after sequential B→C updates |
|---|---:|---:|
| A (base) | 0.9438 | 0.0405 |
| B | 0.9492 | 0.0007 |
| C | 0.9150 | 0.9370 |

Reported routed accuracies exceed the 0.90 threshold, and reported shared-control B falls below 0.90. Six invalid routes yielded; the frozen base remained tensor-identical. Adapter trainable tensors in each snapshot round-tripped and rolled back tensor-exactly. These observed results do not satisfy the full state_dict clarification, so they do not justify a formal PASS.

Recorded training: base pretrain 247.95 ms; separate B/C adapter updates 141.22/140.30 ms; shared adapter B/C updates 146.95/131.29 ms. Each adapter has 40 trainable parameters and snapshot payloads were 1,496 bytes. Adapter setup time was not measured. Dispatcher-only median was 0.0001375 ms/call, excluding inference and model loading. CUDA peak allocated was 69,009,408 bytes.

## Reproduce / audit

- [PRE-REGISTRATION.md](PRE-REGISTRATION.md): frozen H/T/D/C/U, split, seeds, gate, hardware and stop rule.
- [runner.py](runner.py): exact frozen formal runner (SHA-256 `4081a3d1e7f353440a2bd6ab45f7d030f6dcfba0f52cfb904c99e79a2fb1cb1e`).
- [RESULT.json](RESULT.json): retained measurements, dataset hashes, snapshot hashes, route outcomes and limits.
- [audit.py](audit.py): offline structural/result-shape audit only; it does not regenerate data or independently recompute reported accuracies (per-row predictions were not retained). It reads a JSON object on stdin with base64 fields `runner_b64`, `result_b64`, and `prereg_b64`; it verifies the frozen source hash, result gates and evidence structure without repeating the formal allocation.

## Interpretation and limits

Treat the accuracy values as contemporaneous runner output, not independently recomputed evidence. This remains a supplemental held result until a reviewable successor addresses the full-state snapshot requirement without repeating this no-retry allocation.

The recorded shared-adapter B competence collapsed after sequential C updates and A competence was also lost; separately routed aggregate scores met the numeric threshold. Because the full-state snapshot condition was not established, these metrics remain supplemental observations rather than a formal pass. They are consistent with per-skill routing helping on this synthetic seed, but do not establish realistic skill transfer, robust continual learning, multi-user concurrency, crash-safe persistence, model-load performance, runtime integration, GUI usefulness, or action safety.
