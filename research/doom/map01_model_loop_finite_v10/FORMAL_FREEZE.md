# MAP01 lease-refresh formal allocation freeze — seed 990636

Issue: [#4513](https://github.com/Unjuno/agent-interface/issues/4513)
Predecessor: [#4484](https://github.com/Unjuno/agent-interface/issues/4484), preserved as infrastructure HOLD.

## H/T/D/C/U

- **H:** Replacing only the inter-segment observe-only lease horizon from 5 seconds to 15 seconds removes the specific post-clock-probe margin conflict, allowing the no-visible-effect contingency refresh to complete and the guarded model-in-loop controller to continue to at least one later model-authored action.
- **T:** One fresh MAP01 OrbStack allocation, seed `990636`, new output `research/doom/map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-01`; at most 24 decisions, `gpt-5.6-luna`/low, session span 4, skill 1, ViZDoom 1.3.0 at 35 tics/s.
- **D:** Scoped primary PASS only if the 15-second observe-only refresh is admitted and completes, and at least one subsequent model-authored action completes with fresh observations and verified empty owner releases. Any incomplete model/admission/clock/transport/container/score evidence is HOLD, not gameplay FAIL. No MAP01 completion claim without independent score evidence. Any unverified physical release is STOP.
- **C:** Preserve controller policy and all 20 runtime inputs from v9. The sole effective-controller source edit is the exact unique literal replacement `"valid_until_ns":clock_ns+5_000_000_000` → `"valid_until_ns":clock_ns+15_000_000_000`. Keep the >=5-second post-probe margin, three clock probes, 30-second executor cap, freshness, typed observations, bounded input, and release checks unchanged. Pinned-container regressions passed before allocation: 5 existing controller/HUD tests and 3 new Executor lease-boundary tests. Source manifest: 20/20 match main `175ff6fff032d43de826d4ea63774cd001df5636`; the six-commit main advance since initial freeze did not change `research/doom` or `research/live_control`. GitHub open/closed Issue searches for seed `990636` and v10 output path, all-state PR search, branch search, and local output-path check found no collision. Formal allocation is exactly once; never retry or reuse seed/path.
- **U:** One run tests this timing gate and bounded continuation only. It cannot establish general gameplay efficacy, reliability, or a population success rate.

## Frozen identities

- Base commit: `175ff6fff032d43de826d4ea63774cd001df5636`.
- v10 adapter SHA-256: `ad5544726e72de94afb7c3fb9d09328035b2602154feaa066ed35c0ec8de58f1`.
- v7 adapter SHA-256: `a92be1f3dbfc8c64f58287188d75db6081987245c9267791b7de05a69d7d6447`.
- Generated effective controller SHA-256: `81eeadd9626c064ad18de15d80a08c0a3c986f93d6e6c83c777be71b315d1e39`.
- Base controller SHA-256: `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`.
- v3/v5/v6 adapter SHA-256: `05a1a02500a3343bab258595d0dae710626c6887144ccc628fb1cfacfb0d1de6` / `a46cd1dcdaa7aac72de49abda5a4e50970984e3660fd0848ccc23c9353c4d9d4` / `02bb2323cbb9bf389f188fec355536a9597f6f8942ff308dd63150d066c9cdcb`.
- All 20 runtime source entries in the retained v9 manifest match this base commit.
- Runtime image: `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`, `linux/arm64`, network disabled, read-only root, bounded tmpfs.
- WAD SHA-256: `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b` (28,787,748 bytes).
- Before allocation, ordinary model usage was allowed; weekly window used 12%, no reset credit was consumed.

## Exact formal invocation (one-time)

```sh
env PYTHONDONTWRITEBYTECODE=1 /Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B research/doom/map01_model_loop_finite_v10/adapter.py --out research/doom/map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-01 --iterations 24 --seed 990636 --session-span 4 --model gpt-5.6-luna --effort low
```

The output directory was absent at freeze. Once invoked, the allocation is permanently consumed, irrespective of outcome. Preserve all raw bytes and stop reason; audit read-only.
