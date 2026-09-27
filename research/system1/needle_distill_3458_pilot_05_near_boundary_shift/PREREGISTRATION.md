# Preregistration — Issue #3847

Canonical H/T/D/C/U was posted before allocation to https://github.com/Unjuno/agent-interface/issues/3847. Allocation: `needle-intent-distill-3458-pilot-05-near-boundary-shift`. Source branch starts at main `a6562cc9ab4892e56016de3c79bb0a13d30d98d3`.

Pilot-04's three-seed PASS applies only to its balanced training-like synthetic generator. This experiment tests a new, in-envelope covariate shift: the CORRECT class is concentrated in `abs(dx) in [0.071, 0.149]`, just outside the deterministic YIELD margin around `abs(dx)=0.06`, while the training CORRECT generator uses `abs(dx) >= 0.15`. CONTINUE and WATCH classes are balanced, independently seeded controls. An IID suite and exact 1,536-row boundary suite are retained per seed.

The only model change is training on the exact pilot-04 generator with fresh seeds 3464, 3465, 3466. Architecture is 6→16→16→3 tanh MLP, AdamW lr 0.008, 700 steps, batch 64, with deterministic algorithms and one CPU thread. The hybrid deterministic metadata/range/margin guard is byte-for-byte behavior-equivalent to pilot-04: invalid evidence or margins always YIELD; learned outputs are proposals only.

## Frozen gates

Each seed's shifted suite must independently reach accepted accuracy >=0.95, accepted coverage >=0.75 and accepted recall >=0.95 in each class, false CORRECT <=0.5% of accepted rows, all 1,536 boundary rows YIELD, all 5 invalid controls YIELD, and CPU single-row p95 <60 ms over 2,000 samples. IID is diagnostic only. Any miss is retained as FAIL/HOLD; source/environment problems are STOP. Exactly one formal runner process, no retries or tuning.

Scope is the hand-authored synthetic teacher only. No Astra annotations, pixels, GUI, action, effect, runtime integration, model authority, or product claim.
