# Issue #59 — posthoc ammo timeline in retained v39 fire-cover windows

## H / T / D / C / U

**H.** Retained v39 intervals with an active `retreat_fire` cover may contain fresh ammo decreases while inference is pending, but the one retained episode may not reach zero ammo; aggregate end-of-run scoring may be unable to attribute useful effects to a particular window.

**T.** This is an explicitly posthoc, read-only source-bound reanalysis, not a prospective allocation. Pin the current-main report and runtime event JSONL blobs at the exact commit in `FREEZE.json`; filter typed observations by each decision's model-wait interval only when the corresponding prior cover contains a fire action. Summarize ammo/health endpoints, decrements, invalidation signal, and event types. The candidate and auditor read the Git blobs without materializing or altering them.

**D.** Classify direct ammo-zero exposure only if an in-window typed ammo value reaches zero. Report `NO_ZERO_EXPOSURE` otherwise. Separately count ammunition decreases and health-triggered policy invalidations. Do not use a terminal aggregate score to infer per-window usefulness.

**C.** HUD values may not establish that a physical fire key was held throughout an interval; decrements can arise from other causes. This was one gameplay trajectory, and no counterfactual policy or causal effect is available.

**U.** Posthoc telemetry reconstruction only. No candidate/controller/game/model/GUI/input rerun. No causal firing, benefit, harm, survival, or MAP01-clear claim. It cannot grant the separate live allocation required by Issue #59.

## Why posthoc

An initial targeted read established that three active fire-cover windows had nonzero ammo decreases. This package makes that exploratory finding reproducible and independently audited, but it is not preregistered and must not be described as one.

## Versioned audit follow-up

The original `audit.py` and `AUDIT.json` are preserved as v1 historical evidence. An independent mutation review found that v1 did not compare several reported window fields or the human-readable disposition against the pinned trace. `audit_v2.py` and `AUDIT_V2.json` add those comparisons without changing `RESULT.json`, the source freeze, or the historical v1 output. `test_audit_v2.py` verifies the unmodified result and rejects five isolated mutations: disposition, health endpoints, invalidation signal, model-wait duration, and cover actions. This repairs audit coverage only; it does not alter the posthoc scientific limitations above.
