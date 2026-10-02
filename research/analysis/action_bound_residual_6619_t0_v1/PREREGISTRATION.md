# Preregistration — Issue #6619 T0

## H / T / D / C / U

- **H:** At equal alarm budget, binding a conservative image residual to the actual delivered pan can improve deadline-bounded detection opportunity for independent events over raw-delta and action-agnostic registration, without losing a critical cue. Null: it adds no value. This synthetic test cannot adjudicate natural imagery.
- **T0:** Deterministic 32x24 grayscale synthetic raster traces; action `pan` or `none`; explicit requested/actual delivery receipt and source generation. Four arms: raw difference, action-agnostic translation fit, receipt-bound translation envelope, and sham/misbound receipt. Cases cross exact/under/over/delayed/failed delivery, external scroll, moving object, one-pixel flash, critical cue, parallax/nonrigid changes, occlusion, and stale focus/generation. All events and non-events stay in the denominator. Candidate emits advisory alarm masks only; safety comparator is full-frame event detection. Frozen alarm budget is 4 cells/trace and event deadlines are two frames after onset. No model, GUI, live game, physical input, or external effects.
- **Independent audit:** Separate raw-only auditor reads frozen fixture plus raw candidate output, reconstructs each frame, receipt validity, action transform, predicted mask, residual, alarm budget, deadline recall, and critical-cue retention. Five mutations: substitute receipt, erase tiny cue, suppress critical cue, accept stale source, and exceed alarm budget. Auditor source is structurally independent from candidate; its own construction tests do not count as the formal audit.
- **D:** `METHOD_PASS_SCOPED` only for exact source/receipt/frame accounting and rejection of every mutation. `H_PASS_SCOPED` only if the preregistered held-out exogenous event is detected by the action-bound arm by deadline and the matched-budget comparator misses it, with no critical misses across all arms. `H_FAIL_SCOPED` if no incremental held-out benefit or any critical miss. `HOLD_IDENTIFIABILITY` if a cue is indistinguishable in the declared observations. Otherwise retain typed STOP/FAIL; no retries or post-hoc threshold changes.
- **C:** Finite axis-aligned translation fixtures may favor the bound arm; action-agnostic registration can perform equally well. Hard alarms may exhaust the budget.
- **U:** No real screenshot or application, event prevalence, actual delivery latency, model attention, safety, game outcome, or product benefit is inferred. A receipt is only a synthetic fixture datum.

## Freeze and execution contract

Branch: `research/action-bound-residual-6619-t0-wslc-20261002`. Base: `87d5699db` (current `origin/main` at preregistration). Additive output directory: `research/analysis/action_bound_residual_6619_t0_v1/formal_01_20261002/`.

One `wslc.exe run --pull never --network none` invocation each for candidate and independent auditor, pinned local Python image `python:3.12-slim` (image ID and inspect to be recorded), input mounted read-only and output on its own mount. No existing containers stopped or modified. CPU-only; do not request GPU. WSLc warning about cgroup/swap limits, if emitted, will be preserved and no enforcement beyond observed evidence claimed. Formal raw and auditor runs happen once each; failures are retained and not silently rerun.

This protocol and fixture are hashed before formal execution. Construction tests are not formal efficacy evidence.
