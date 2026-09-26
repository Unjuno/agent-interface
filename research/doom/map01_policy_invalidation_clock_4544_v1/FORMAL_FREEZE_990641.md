# Issue #4544 formal allocation freeze — seed 990641

Status: preregistered; formal invocation not yet started.

Base: current main `13cd6645b1bdd266bbe010f82ebcec2a573c23ed` (2026-09-27).
Predecessors #4513, #4516, #4536, and PR #4542 remain unchanged. The failed
#4536 formal seed `990639` is consumed and retained; this is a genuinely new
allocation for the enriched monitor-receipt contract.

## H/T/D/C/U

- **H:** Accepting required monitor invalidation fields while preserving the
  monitor's additional metadata allows the host timestamp to be translated into
  runtime monotonic time. The stale interrupted planner action is rejected
  before executor admission, and a later fresh decision can proceed.
- **T:** One new pinned MAP01 allocation, seed `990641`, at most 24 decisions,
  model `gpt-5.6-luna`/low, session span 4, skill 1. Output:
  `research/doom/map01_policy_invalidation_clock_4544_v1/results/map01-model-loop-finite-v12-20260927-04`.
- **D:** Scoped allocation PASS requires an actually captured enriched monitor
  receipt, preserved host and runtime copies with same-session three-probe
  provenance, `REJECTED_POLICY_INVALIDATED` and no executor admission/input for
  the stale action, a later fresh planner action admitted and completed without
  clock exception, and verified empty owner releases. All 24 decisions must
  complete for allocation-level PASS. No invalidation or incomplete horizon is
  HOLD; receipt-contract error or unverified release is STOP. No MAP01 exit
  inference without independent score evidence. No retry.
- **C:** Keep shared v39/v10/controller/runtime sources unchanged. The sole
  effective controller delta remains final-admission receipt translation using
  `clock_translation_v2.py`. Preserve monitor metadata, original host timestamp,
  runtime timestamp, clock samples, 15s observe refresh, <=1s uncertainty,
  <=5s calibration age, >=5s lease margin, 30s executor cap, freshness, typed
  observations, bounded inputs, and independent release. Full source mount;
  pinned image network-disabled and read-only.
- **U:** #4536's exact invalidation status/time was not persisted; the production
  shape tested here is synthetic around a retained real calibration record.
  Whether this corrected conversion works in formal execution, sustains later
  actions/full horizon, or affects gameplay remains unknown.

## Construction and preflight gates

- Pinned Docker regression: 19/19 tests pass, including 4 enriched-receipt
  tests, 6 #4536 mechanism tests, 3 v10 refresh tests, and 6 existing final
  admission tests. Container was `linux/arm64`, `--network none`, read-only
  root and read-only repo mount. Effective candidate controller AST passed.
- The enriched receipt test first confirms the old v1 helper rejects the
  production-shaped monitor object, then proves v2 preserves all fields and
  changes only timestamp value/domain, ending in
  `REJECTED_POLICY_INVALIDATED` with no executor admission. Its missing
  historical event time remains explicitly synthetic.
- Fresh zero-model MAP01 preflight (seed `990640`) reached ready, completed an
  observe-only control, verified 3/3 actual owner releases empty, and recorded
  zero model turns. This is not gameplay/formal evidence.
- Runtime image:
  `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`
  (`linux/arm64`). WAD SHA-256:
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Runtime 20-source manifest SHA-256:
  `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`.

## Frozen source identities

- v2 successor adapter: `5ac4aa691cb62da7e7b444b2f9452815bfd79ed14b720cdefd49259448b3e6c5`
- v2 translator: `99ca937e911b89c1613f5be504ea64b416d98fe685a27f796900e44df887dfb0`
- v2 deterministic tests: `48a40d321dc25e531ea2aa9224b482e344bad1db681e3f2f72e813f01c99f6c0`
- effective candidate controller: `53deb212a722f9d38d55e85d30eb9375ed3761c82c1f66554dbc4842931f7eeb`
- v10 adapter: `ad5544726e72de94afb7c3fb9d09328035b2602154feaa066ed35c0ec8de58f1`
- v7 adapter: `a92be1f3dbfc8c64f58287188d75db6081987245c9267791b7de05a69d7d6447`
- unchanged v39 controller: `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`

## Exact one-time invocation

```sh
env PYTHONDONTWRITEBYTECODE=1 /Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B research/doom/map01_policy_invalidation_clock_4544_v1/adapter_v2.py --out research/doom/map01_policy_invalidation_clock_4544_v1/results/map01-model-loop-finite-v12-20260927-04 --iterations 24 --seed 990641 --session-span 4 --model gpt-5.6-luna --effort low
```

Open/closed Issue queries for seed `990640`/`990641` and the exact formal
output path, all-state PR query, branch searches, and local exact-seed/path
checks found no collision. Formal output path was absent at freeze time. The
separate zero-model preflight used seed `990640`; it consumed no model/formal
allocation.
