# MAP01 lease-refresh formal allocation freeze — seed 990637

Issue: [#4516](https://github.com/Unjuno/agent-interface/issues/4516)
Prior allocation #4513 / seed 990636 is a preserved pre-game source-mount STOP; it is never retried.

## H/T/D/C/U

- **H:** Replacing only the inter-segment observe-only lease horizon from 5 seconds to 15 seconds removes the strict post-clock-probe margin conflict, allowing the no-visible-effect contingency refresh and at least one subsequent model-authored action to complete.
- **T:** One fresh MAP01 OrbStack allocation, seed `990637`, output `research/doom/map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-02`; max 24 decisions, `gpt-5.6-luna`/low, session span 4, skill 1.
- **D:** Scoped PASS only if the 15-second refresh is accepted and completes and at least one subsequent model-authored action completes with fresh typed observations and verified empty owner releases. Incomplete model/admission/clock/transport/container/score evidence is HOLD, not gameplay FAIL. No map-exit claim without an independent score. Any unverified physical release is STOP.
- **C:** Preserve the v39 controller policy and all 20 v9 runtime source identities. The sole effective-controller change is the exact unique literal replacement `"valid_until_ns":clock_ns+5_000_000_000` → `"valid_until_ns":clock_ns+15_000_000_000`. Keep the three clock probes, >=5-second post-probe margin, 30-second admission cap, freshness, typed observations, bounded input, and release checks unchanged. The mounted non-sparse source set includes `research/doom`, `research/live_control`, `research/observation_tiles`, `research/observation_gating`, and `research/real_apps_v1`; session import/start preflight passed from this exact mount. Pre-allocation container gates: 5 existing controller/HUD tests PASS, 3 Executor lease boundary tests PASS, startup zero-decision preflight PASS (ready, 2 observe-only controls completed, 3/3 empty releases). All 20 runtime manifest hashes match current main. Open/closed Issue queries for seed and exact output path, all-state PR query, branch query, and local path absence check found no collision. Formal allocation exactly once; never retry seed/path.
- **U:** A single bounded allocation establishes only this lease gate and one episode's continuation, not general gameplay success, reliability, or population performance.

## Frozen identities

- Current base main: `c9bfb14c41b9ce72782a03ed4bfa0d814baf6a8f`.
- v10 adapter SHA-256: `ad5544726e72de94afb7c3fb9d09328035b2602154feaa066ed35c0ec8de58f1`.
- v7 adapter SHA-256: `a92be1f3dbfc8c64f58287188d75db6081987245c9267791b7de05a69d7d6447`.
- Generated effective controller SHA-256: `81eeadd9626c064ad18de15d80a08c0a3c986f93d6e6c83c777be71b315d1e39`.
- Unmodified v39 controller SHA-256: `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`.
- Pinned runtime: `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`, `linux/arm64`, `--network none`, read-only root, bounded tmpfs.
- WAD SHA-256: `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`, 28,787,748 bytes.
- Usage at preregistration: ordinary usage allowed; weekly window 12% used; no reset credit consumed.

## Exact one-time invocation

```sh
env PYTHONDONTWRITEBYTECODE=1 /Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B research/doom/map01_model_loop_finite_v10/adapter.py --out research/doom/map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-02 --iterations 24 --seed 990637 --session-span 4 --model gpt-5.6-luna --effort low
```

The output path was absent when frozen. Invocation consumes the allocation even if it stops before gameplay. Preserve all raw files and never retry.
