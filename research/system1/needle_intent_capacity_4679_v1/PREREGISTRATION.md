# Needle counterfactual intent-capacity experiment

Issue #4679; allocation `needle-intent-capacity-4679-v1`.

## H

The #4153 intent-aware delegate materially outperformed its state-only control but the 10→24→24→4 network missed the frozen accuracy, exact-all-intents and disagreeing-intent gates. Hypothesis: widening only the two hidden layers to 64 will close this bounded synthetic held-out fidelity gap under the original #4153 teacher, one-hot intent, dataset sizes and full-batch 900-step AdamW recipe.

## T

Three fresh base seeds: 4153101, 4153103, 4153107. For each seed, train states use the base seed and held-out states use base+1; state-only initialization uses base+10; both intent-aware widths use base+20. Each split has 4096 training and 2048 held-out base states, expanded in fixed order over TRACK, STABILIZE, WATCH_ONLY, OUT_OF_SCOPE and CONTINUE, CORRECT, WATCH, YIELD. Exact #4153 generator and deterministic teacher retained. All arms share the identical state rows/labels.

Arms: STATE_ONLY_24 (6→24→24→4), INTENT_AWARE_24 (10→24→24→4), and INTENT_AWARE_64 (10→64→64→4); two tanh hidden layers. Full-batch cross-entropy AdamW, lr 0.006, weight decay 1e-4, exactly 900 steps per fit. One fit per arm per seed, nine fits total. No retry, tuning, replacement seed, or post-result extension. Invalid/unknown intent interface controls YIELD without model calls.

Authority-neutral synthetic shadow evaluation only. Docker image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Docker 29.8.0, Linux/amd64 CPU, Python 3.12.14, PyTorch 2.5.1+cpu, one CPU/thread, 2 GiB, 64 PIDs, network none, read-only source and root. Trainer and independent auditor are separate containers with isolated output mounts. The runner accepts a host-precreated empty output mount, refuses a nonempty mount, and never overwrites prior output. No GUI, user data, provider, action dispatch, or model promotion.

## D

Each 64-wide seed must meet all #4153 candidate gates: accuracy ≥0.97; exact-all-intents ≥0.90; disagreeing-intent accuracy ≥0.96; OUT_OF_SCOPE YIELD recall ≥0.995; action-on-teacher-YIELD ≤0.01; forbidden-effect proposals ≤0.01. Also require teacher-disagree base fraction ≥0.50, STATE_ONLY_24 exact-all-intents ≤0.60, invalid intent IDs always YIELD, exact prediction recomputation from saved model tensors, and independent audit with zero errors.

- `PASS_CAPACITY_CLOSED_GAP_SCOPED`: 64-wide passes every gate in all seeds and 24-wide fails at least one core accuracy/exact/disagree gate in at least two seeds.
- `PASS_INTENT_FIDELITY_NO_CAPACITY_NEEDED`: both intent-aware widths pass every seed gate.
- `FAIL_CAPACITY_NOT_SUFFICIENT`: the integrity-valid 64-wide candidate fails any required candidate gate in any seed.
- `INCONCLUSIVE_MIXED_CAPACITY`: none of those patterns; retain per-seed metrics without winner selection.
- Any source, execution, or audit-integrity problem is typed STOP, not scientific failure.

## C

Width may not be the cause; failure can reflect seed variance, training dynamics, one-hot representation limits or teacher-boundary complexity. Same optimizer, data sizes, teacher and labels across arms; hidden width is the only candidate architecture treatment. Report fit time/model bytes descriptively, with no post-hoc resource gate.

## U

Three seeds, one synthetic task family, one host/image. One-hot synthetic intents are not natural-language Astra intent. No real Astra demonstrations, GUI semantics, tool execution, online feedback, skill transfer, hardware generalization or runtime/product readiness is established.
