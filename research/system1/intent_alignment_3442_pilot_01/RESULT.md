# Formal outcome — Issue #3442 intent-aligned System-1 pilot 01

Allocation: `intent-aligned-system1-3442-pilot-01`
Branch: `research/intent-aligned-system1-3442-pilot-01`
Frozen runner SHA-256: `83e59427cebcbffa3c7be76e89f4ffe483727cf4f87dc0efb54539b580724751`
Full raw output, including all held-out rows and both model state_dicts: [RESULT.json](RESULT.json)

## Execution and decision

Exactly one formal CPU run completed in memory on the Windows host (Python 3.11.9, PyTorch 2.5.1+cu121, one CPU thread). No CUDA, Docker, local artifacts, GUI, network requests, or action execution. This is not container evidence.

Frozen gates:
- Conditioned accuracy: 0.79297 (required >=0.95) — MISS
- Baseline accuracy: 0.60742; absolute gain: 0.18555 (required >=0.20) — MISS
- Conditioned paired-intent exact: 0.73242 (required >=0.90) — MISS
- CPU inference p95: 0.0281 ms (required <60 ms) — PASS
- Matched gate controls: 1,024/1,024 PROPOSE — PASS
- Stale intent: 1,024/1,024 YIELD — PASS
- Stale evidence: 1,024/1,024 YIELD — PASS
- Unknown intent: 1,024/1,024 YIELD — PASS

Outcome: `HOLD_OR_FAIL_GATE_MISS`. Do not describe this as a successful intent-alignment result. The conditioned network improves over baseline, but it misses all three frozen predictive criteria. Guard behavior is only a synthetic deterministic control result.

## Independent audit status

The frozen independent auditor was launched once against the complete stdout JSON. It received the payload but did not finish in a reasonable time and grew to approximately 1.1 GiB resident memory while recomputing CPU predictions. The auditor process was stopped to contain resource use. Thus source/run hashes and the complete raw output are retained, but independent row/weight/split recomputation is **INCOMPLETE**. This is an integrity HOLD, not a favorable audit and not an additional model run. No retry or tuning was performed.

## Interpretation and next step

This pilot only shows a directionally higher score when the synthetic paired intent bit is supplied; the evidence is insufficient under preregistered gates, and there is no real trajectory, online fine-tuning/LoRA, role-network or skill-reuse evidence. Preserve this run unchanged. A successor allocation may first fix the auditor's computational profile and preregister any changed evaluation; do not overwrite or relabel this result.
