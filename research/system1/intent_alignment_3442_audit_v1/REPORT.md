# Formal audit result — Issue #3849 / predecessor #3442

Allocation: intent-aligned-system1-3442-audit-localdocker-01
Formal invocation: 1; retries: 0
Frozen source commit: 6a1b33e (branch `research/issue-3849-intent-audit-docker-v1`)

## H / T / D / C / U

**H.** A standard-library-only auditor would independently reproduce all held-out labels, predictions, metrics and the retained decision under a 256 MiB container cap.

**T.** Audited the exact #3738 predecessor source/result closure on local Docker Desktop Engine 29.8.0, Linux/amd64, cached image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Source mount and container root were read-only, network disabled, /tmp bounded to 16 MiB, memory capped at 256 MiB, CPUs=2 and pids=32. Exact command and source/result digests are in [FREEZE.json](FREEZE.json). Construction controls passed 6/6 in Docker before freeze. The one formal command is captured byte-for-byte in [FORMAL_STDOUT.jsonl](FORMAL_STDOUT.jsonl).

**D.** `PASS_AUDIT_INTENT_ALIGNMENT_HOLD_SCOPED`. Independent auditor recomputed 1,024 paired rows, all teacher labels and both model prediction vectors; errors=[]; all recorded gates and decision match. It reproduced `HOLD_OR_FAIL_GATE_MISS`, not a model PASS. Accuracy: baseline 0.607421875, conditioned 0.79296875, gain 0.185546875; paired-intent exact: 0.41796875 vs 0.732421875. Conditioned p95: 0.0281 ms. Accuracy, gain and paired exact gates remain false; stale-intent/evidence/unknown YIELD and matched PROPOSE controls remain true. Exact stdout SHA-256 is recorded in SHA256SUMS.

**C.** The original failure may reflect model capacity, optimization, synthetic teacher/data design, or another training factor; this audit does not distinguish them. The compact scalar evaluator reproduces categorical predictions and aggregate results, not bitwise-identical logits or training gradients.

**U.** Posthoc audit of one existing synthetic CPU training result. The PyTorch PRNG split and optimizer trajectory were not independently regenerated. No retraining, CUDA/GPU use, real Astra trajectory, GUI/action execution, local fine-tuning benefit, or runtime safety/authority claim. The #3738 predecessor remains Draft; this successor only validates its retained output and does not alter its result.

## Integrity

- Predecessor Git blob IDs for the copied runner, auditor, preregistration, construction record, result and README are frozen in FREEZE.json; raw RESULT.json Git blob SHA-1 matches the predecessor exactly.
- Raw RESULT.json SHA-256: 0b76acac8b4160b9080476accfb0499b903342d67f8e9e8cb1360428dad019d7.
- Independent corruption controls: wrong raw digest, altered prediction, forged gate, forged outcome, and pair-order corruption all rejected (6/6 total construction tests).
- No source edits after freeze and no formal retries.
