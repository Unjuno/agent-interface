# CACTUS_NEEDLE3 bounded local structured-action discriminator

## H — hypothesis

The local 35 MB Needle 3 base model can produce exact, independently acceptable proposals for a tiny bounded home-control vocabulary, including a two-action request and changed target, while refusing forbidden, ambiguous, stale-scope, and already-satisfied requests. Compare it with a deterministic guarded-macro baseline on the same seven frozen cases. Model proposals never receive OS or real-device authority.

## T — allocation

- Allocation: `cactus-needle3-action-delegate-v1-20260927-01`.
- Issue: #4204; predecessor experiment lineage is not rewritten.
- Branch: `research/cactus-needle3-action-delegate-20260927`.
- Additive path: `research/analysis/cactus_needle3_action_delegate_v1/`.
- Local checkpoint: `Cactus-Compute/needle3`, HF revision `b274efcb211a9eef48c9a88da4b43bd569696a39`, `needle3.cact`, SHA-256 `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38`, 35,335,380 bytes.
- Runtime: `cactus-needle==3.0.1`; package source reference `cactus-compute/needle` main commit `42bf1f2d0a7784b0d4d1ec94bb5ade425cf9a67c`; Python 3.12; base image pinned by local OCI digest in Dockerfile.
- Authority-neutral synthetic fixture, seven fixed cases: nominal light, bounded two-action light+thermostat, changed target, forbidden schedule deletion, missing/ambiguous target, stale scope version, and already-satisfied/no-op.
- Same natural-language requests and visible state go to the guarded macro and model. The macro uses only frozen regex/guard rules; the model uses the same fixed tool vocabulary and exact typed schemas.
- Each proposed call is only recorded. The local evaluator separately checks scope/freshness, allowlist, grounded arguments, order, and expected final synthetic state. No GUI, network-connected tool, user data, real effect, or execution authority is exposed.
- One fresh formal container process; one pass over all seven cases; no tuning, retries, prompt changes, or case replacement. Construction tests and one non-scored smoke call are excluded and retained separately.

## D — frozen decisions and measures

Record exact schema validity, per-case proposal list, macro/model semantic match, action and argument correctness, required YIELD/refusal, forbidden proposal and externally rejected proposal counts, simulated final state, warm decision p50/p95, first/cold-case latency, initialization time, peak RSS, package/model/image hashes, and all raw responses.

- `PASS_CACTUS_NEEDLE3_ACTION_DELEGATE_SCOPED`: model exactly matches all three actionable cases, yields on all four negative/no-op cases, has zero forbidden or stale proposals, completes verified synthetic work, and warm p95 is <=2,000 ms.
- `FAIL_CACTUS_NEEDLE3_ACTION_FIDELITY`: any integrity-valid wrong tool/argument/order/final synthetic state on the three actionable cases.
- `FAIL_CACTUS_NEEDLE3_YIELD_BOUNDARY`: any proposal on forbidden, ambiguous, stale, or no-op cases; any unauthorized proposal remains a model-quality failure even if the external guard rejects it.
- `HOLD_LATENCY_ONLY_SKILL_EXECUTOR`: all semantic/YIELD gates pass but warm p95 exceeds 2,000 ms.
- `FAIL_NO_VALUE_OVER_EXPLICIT_BASELINE`: the macro matches the full frozen contract and Needle fails any gate; also report the latency/correctness delta without treating the macro as a model.
- `STOP_MODEL_OR_PROVENANCE_UNAVAILABLE`: exact local weights, pinned package/image, offline engine, source hashes, or output evidence cannot be verified.

The explicit baseline is expected to be faster; this first rung asks whether the model is a viable bounded proposal source, not whether it should replace the macro.

## C — constraints

Use local Docker Desktop only, CPU inference, 2 vCPUs / 2 GiB memory / 64 PIDs, network disabled for the formal run, read-only root/model/source/runtime-cache mounts, 64 MiB `/tmp`, dedicated writable output mount. No package install during formal, no provider/API/model runner, no GPU, no GUI/input, no persistent runtime state, no cloud/HF Jobs. Disable anonymous telemetry. The container's proposal callbacks/evaluator cannot mutate the host or access OS input.

## U — limits

One synthetic home-control vocabulary, seven hand-authored cases, one cached quantized checkpoint, one CPU host. No natural error rate, open-world generalization, real application effect, human-tempo, product safety, or model promotion claim. This base discriminator is a prerequisite for considering #4205 adaptation; it does not itself test training or fine-tuning.
