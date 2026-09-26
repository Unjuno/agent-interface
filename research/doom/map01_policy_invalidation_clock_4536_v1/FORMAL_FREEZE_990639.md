# Issue #4536 formal allocation freeze — seed 990639

Status: preregistered; formal invocation not yet started.

Predecessors #4513/#4516 and PR #4532 remain immutable. The local fast-forward
base is `22e9c43503109277073d7b2b667c354ef60bbba3` (main, 2026-09-27). The
experiment modifies no shared runtime/controller source; its adapter and
clock helper live only under this successor directory.

## H/T/D/C/U

- **H:** Translating only the policy monitor's host-monotonic
  `outcome_evaluated_ns` with the conservative lower bound of the exact
  same-session decision-clock probes prevents the mixed-domain ordering error.
  The interrupted/stale planner answer is rejected before Executor admission;
  a subsequent fresh decision can proceed under existing guards.
- **T:** One fresh pinned MAP01 formal allocation, seed `990639`, up to 24
  decisions, model `gpt-5.6-luna`/low, session span 4, skill 1. Output:
  `research/doom/map01_policy_invalidation_clock_4536_v1/results/map01-model-loop-finite-v11-20260927-03`.
- **D:** Formal scoped PASS requires a persisted actual invalidation receipt in
  both domains, same-session calibration provenance, stale planner rejection
  (`REJECTED_POLICY_INVALIDATED`, no executor admission/input), a later fresh
  planner action admitted and completed without the boundary exception, and
  verified empty owner releases. All 24 decisions must complete for the
  allocation-level PASS. Missing invalidation, partial horizon, calibration or
  receipt uncertainty is HOLD; unverified release is STOP. No MAP01 exit claim
  without independent score evidence. No retry under any outcome.
- **C:** Retain the 15-second observe-only refresh, three decision clock probes,
  <=1-second offset uncertainty, <=5-second invalidation-to-calibration age,
  >=5-second lease margin, 30-second executor cap, freshness/typed-observation
  gates, bounded inputs, and independent owner release. Only the final
  admission boundary receives a translated copy; raw host receipt is preserved
  beside the runtime copy. Main controller v39 and v10 predecessor remain
  unchanged. Full source mount; container image network disabled and read-only.
- **U:** The missing predecessor invalidation receipt prevents retrospective
  proof that it caused #4516's exception. Whether one translation suffices for
  a full 24-decision allocation, whether gameplay progresses, and whether MAP01
  exits remain unknown.

## Construction and preflight gates

- Deterministic regression: 6/6 new tests pass locally and in the pinned
  container; 3/3 existing refresh tests and 6/6 existing final-admission tests
  pass in the same container (15/15 total). The historical decision-8 probe
  set and recorded planner/controller runtime timestamps are used; the missing
  invalidation timestamp in that counterexample is explicitly synthetic.
- Effective candidate controller parses successfully and hashes to
  `d46fc912512d60c48fe897a4786ca0b9c8319ae681b9412482835085c946fcd4`.
- Zero-model MAP01 preflight reached ready, accepted/completed an observe-only
  control, recorded three verified empty owner releases, and used zero model
  turns. This is startup/release evidence only, not formal gameplay evidence.
- Cached runtime image:
  `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`
  (`linux/arm64`); network disabled, root read-only.
- WAD SHA-256: `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Runtime source manifest SHA-256:
  `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`.

## Frozen source identities

- Successor adapter: `51adcdea6bb4b9cde87b8ede6e4dc79c6edcfe696d1aad2e4c7443c30cbe2ccd`
- Translation helper: `4b585e7373880d7306d38cb3bfeb5d36b85244457e5963f6218bc9ae12510b4f`
- Effective candidate controller: `d46fc912512d60c48fe897a4786ca0b9c8319ae681b9412482835085c946fcd4`
- v10 adapter: `ad5544726e72de94afb7c3fb9d09328035b2602154feaa066ed35c0ec8de58f1`
- v7 adapter: `a92be1f3dbfc8c64f58287188d75db6081987245c9267791b7de05a69d7d6447`
- unchanged v39 controller: `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`

## Exact one-time invocation

```sh
env PYTHONDONTWRITEBYTECODE=1 /Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B research/doom/map01_policy_invalidation_clock_4536_v1/adapter.py --out research/doom/map01_policy_invalidation_clock_4536_v1/results/map01-model-loop-finite-v11-20260927-03 --iterations 24 --seed 990639 --session-span 4 --model gpt-5.6-luna --effort low
```

Issue/PR open+closed searches, branch search, and local tracked/untracked path
checks found no collision for seed `990639` or the exact output path. The path
was absent at freeze time. The separate zero-model startup preflight used seed
`990638`; no model decision or formal allocation was consumed there.
