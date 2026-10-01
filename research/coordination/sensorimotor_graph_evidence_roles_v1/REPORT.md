# Typed evidence roles for sensorimotor graphs

Task: `SENSORIMOTOR-GRAPH-EVIDENCE-ROLE-TYPING-20260917-001`, Issue #745.

**Decision: `PASS_TYPED_EVIDENCE_ROLE_GATE_SCOPED`.**

## Question
Can a graph validator prevent weak evidence roles from being silently promoted into actuator authority while preserving legitimate revalidation and non-actuating uses?

## Method
Container-only deterministic fixture. Same ten authored graph scenarios and same executor under two validators:

- `structural_only`: checks finite structure/resources/cleanup only;
- `typed_roles`: additionally propagates role + freshness.

Formal block: 10 scenarios x 4 repetitions x 2 validators = **80 first rows**, one runner invocation, no rerun/replacement/tuning.

Safe scenarios: current admission -> actuator; historical hint + current evidence -> `REVALIDATE_CURRENT` -> admission -> actuator; current invalidator -> planner context -> yield; current effect evidence -> terminal success; historical hint -> planner context -> yield.

Unsafe scenarios: direct HINT / PLANNER_CONTEXT / INVALIDATOR / EFFECT_EVIDENCE -> ACTUATOR, plus historical ADMISSION_DEPENDENCY -> ACTUATOR.

## Result
- typed safe acceptance: **20/20**;
- typed unsafe pre-input rejection: **20/20**;
- structural baseline unsafe backend emissions: **20/20** (intentional negative controls);
- safe runtime outputs match across validators: **20/20**;
- frozen audit errors: **0**.

The typed validator is therefore not merely more conservative: it preserves every authored safe route while preventing all authored authority-laundering routes before executor/backend invocation.

Specific rejection rules:
- HINT/PLANNER_CONTEXT/INVALIDATOR/EFFECT_EVIDENCE cannot directly feed ACTUATOR: `ACTUATOR_REQUIRES_ADMISSION_DEPENDENCY`;
- historical admission evidence cannot actuate: `ACTUATOR_REQUIRES_CURRENT`;
- a historical HINT may become current admission only through explicit `REVALIDATE_CURRENT` paired with a current admission dependency.

## ERROR CHECK
- postformal independent verifier: PASS, errors 0;
- copied-evidence corruption controls rejected **7/7**;
- postformal source hashes still match preregistration;
- unit tests re-pass **7/7**.

Formal result SHA-256: `87dcf40010d132d0b422bd063fac0e33aed879250e90daf9370a1ace4fb04cb3`.
Audit SHA-256: `06ed6779e6bc926fbdaaf356560ac80323368f9b40c81be8f2ee17095cc188b0`.
Postformal verifier SHA-256: `efb1eba7121747bf489c992919372ce21509cc2831f95fd8b6e3a1530baa9444`.
Corruption controls SHA-256: `a26a414504d1e4df305b23c6149035638861b39f7cd4f3d2b5337523e5d63d25`.

## H / T / D / C / U
**H:** evidence role/freshness typing blocks authority laundering without rejecting safe explicit promotion.

**T:** authored deterministic graph IR; 80 rows; one variable is validator policy.

**D:** `PASS_TYPED_EVIDENCE_ROLE_GATE_SCOPED`.

**C:** the role taxonomy and legal promotion table are authored. A richer graph language may expose missing roles or cases that need dynamic checks rather than static typing.

**U:** no GUI, model, network, concurrency, performance, or production-security claim. This establishes a static graph-IR discipline only.

## Next question
Transfer the same typed-role rule into one real graph execution where a cached HINT is revalidated against current pixels before an actuator, keeping the untyped direct-hint path as the negative control. Do not expand the role vocabulary until a retained task requires it.
