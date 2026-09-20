# Per-skill LoRA routing — Issue #3701

Successor to #3441 pilots 01–03. This is a synthetic component experiment only; earlier results are preserved unchanged.

## Result

`PASS_MULTI_SKILL_ROUTING_SCOPED` on one preregistered Windows-host RTX 3080 Laptop GPU allocation (PyTorch 2.5.1+cu121, CUDA 12.1). The Docker Desktop daemon was unavailable; this is explicitly not a container result.

| Held-out skill | Explicit per-skill route | One shared adapter after sequential B→C updates |
|---|---:|---:|
| A (base) | 0.9438 | 0.0405 |
| B | 0.9492 | 0.0007 |
| C | 0.9150 | 0.9370 |

All explicit routes exceed the preregistered 0.90 threshold. Six unknown/stale/missing/wrong route controls yielded. The frozen base remained tensor-identical. Each of three learned snapshots round-tripped tensor-by-tensor exactly; each pre-update rollback restored every adapter tensor exactly.

Training: base pretrain 247.95 ms; separate B/C adapter updates 141.22/140.30 ms; shared adapter B/C updates 146.95/131.29 ms. Snapshot payloads were 1,496 bytes each. Dispatcher-only median was 0.0001375 ms/call, excluding inference and model loading. CUDA peak allocated was 69,009,408 bytes.

## Reproduce / audit

- [PRE-REGISTRATION.md](PRE-REGISTRATION.md): frozen H/T/D/C/U, split, seeds, gate, hardware and stop rule.
- [runner.py](runner.py): exact frozen formal runner (SHA-256 `4081a3d1e7f353440a2bd6ab45f7d030f6dcfba0f52cfb904c99e79a2fb1cb1e`).
- [RESULT.json](RESULT.json): retained measurements, dataset hashes, snapshot hashes, route outcomes and limits.
- [audit.py](audit.py): independent offline structural audit. It reads a JSON object on stdin with base64 fields `runner_b64`, `result_b64`, and `prereg_b64`; it verifies the frozen source hash, result gates and evidence structure without repeating the formal allocation.

## Interpretation and limits

The shared adapter's B competence collapsed after sequential C updates and A competence was also lost, while separately routed adapters passed this small test. This supports the narrow hypothesis that explicit per-skill adapters avoid this particular synthetic interference pattern. It does not establish realistic skill transfer, robust continual learning, multi-user concurrency, crash-safe persistence, model-load performance, runtime integration, GUI usefulness, or action safety. One synthetic seed is not a generalization result.
