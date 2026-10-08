# H/T/D/C/U — #4899

## H — hypothesis

A fail-closed role network that routes A to an immutable A skill and B to a distinct online rank-2 LoRA skill will retain A while acquiring B, outperforming shared-adapter online and fixed A-replay packages. This is a combined role-routing/adapter-isolation package test; the supplied synthetic role bit is not natural-language role inference.

## T — frozen treatment

- Allocation: `needle-role-router-online-lora-replay-20260927-v1`; formal seeds 736211, 736311, 736411; excluded construction seed 736014.
- Disjoint A base train (256 rows, 400 single-row AdamW updates), A memory (16), B support (16), held-out A (256), held-out B (256); role is explicit feature 9; A label = feature 1, B label = 1 − feature 1.
- Four paired arms, same base and adapter initial tensors, B support/order and 16×8 = 128 update budget: `SHARED_B_ONLY`; `SHARED_A_REPLAY` pairs each B row with cyclic A memory; `ROUTED_SHARED_ADAPTER`; `ROUTED_SEPARATE_SKILLS` keeps A adapter immutable and routes only B corrections to independent B adapter/AdamW state.
- Role receipt binds allowed role, synthetic scope and graph generation. Unknown/stale/wrong-scope controls must YIELD without adapter selection/proposal. Record route receipts, both skill states, optimizer state, predictions, timings, hashes, Docker argv/stdout/stderr, and one separate raw-only deterministic reconstruction.
- Cached CPU image pinned by immutable digest; no pull/network; source/root readonly; 1 CPU, 2 GiB, 64 PIDs. Freeze has source SHA-256s and exact bare-hex sidecar.

## D — decisions

- `PASS_ROUTED_ONLINE_LORA_SKILLS_SCOPED`: all three seeds replay with zero audit errors; frozen base and A skill stay immutable; all invalid-route controls YIELD without proposal; every update is <60 ms; separate-skill final held-out A and B >=0.90 on each seed; A >=0.10 above **each** of `SHARED_B_ONLY`, `SHARED_A_REPLAY`, and `ROUTED_SHARED_ADAPTER` on every seed; B within 0.10 of best shared-online B.
- `FAIL_ROUTING_OR_RETENTION`: valid independently audited formal run misses any quality gate.
- `HOLD_AUDIT_INTEGRITY`: provenance/reconstruction/auditor integrity defect; do not reinterpret as a model-quality FAIL.
- Typed `STOP_*`: source/image/allocation/resource/collision failure before a valid fit. One formal orchestration only; no retry, tuning or seed substitution.

## C — alternatives and confounders

Separate skills change parameter count, routing and AdamW-history isolation together; this cannot identify which component caused any difference. Fixed rehearsal changes the training objective and update batch shape. Different batch shapes can produce numerical trajectory differences, so audit each arm against its own reconstruction and only test explicit mathematical equivalence with a stated tolerance. Synthetic labels are intentionally simple and the role is handed to the router.

## U — limits

Three local CPU seeds; synthetic explicit role; small 16-hidden/4-logit model; no live Needle/agent interaction, natural-language routing, user task utility, broad transfer, durable updates, GUI integration, safety/action authority or production claim.
