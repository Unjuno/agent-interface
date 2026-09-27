# Guard-policy calibration identifiability R1 — retained result

Issue #1672. Direct predecessor #1646 fixed the recoverable-route break-even selector.

## Disposition

**PASS_RETAINED_GUARD_CALIBRATION_NOT_IDENTIFIABLE_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

This is an identifiability result, not a guard-policy recommendation.

## Question

Can any retained route populate all seven quantities required by #1646 in one same-population, commensurate cost model?

Required selector inputs:

- `c_g` — pre-guard acquisition/validation cost;
- `p` — stale-at-admission incidence for the route population;
- `s` — stale-detection sensitivity;
- `f` — fresh false-reject rate;
- `c_y_stale` — true-stale reject/yield/replan cost;
- `c_y_fresh` — fresh false-reject cost;
- `c_f` — stale-action failure+recovery cost.

Cross-route substitution is forbidden. Hard correctness/safety effects remain outside finite expected-cost optimization.

## Retained families inspected

| Family | Useful retained evidence | Blocking calibration evidence |
|---|---|---|
| #1179 / PR #1369 | AF_UNIX guard acquisition p95 0.039589 ms; exact synthetic dispositions | stale schedule is authored, not empirical `p`; no planner yield costs; no stale task-effect recovery cost |
| #1172 / PR #1186 | private-X11 ROI guard p95 0.221238 ms; exact controlled classifier behavior | stale schedule authored; invalidation-to-stop is not planner yield cost; no task failure/recovery cost |
| #1163 | action-time guard prevents synthetic HARD/AMBIG effects | live `c_g` absent in this allocation; stale schedule authored; HARD effects are a hard correctness contract, outside finite `c_f` selector |
| #659 → #663 | stale cached route hits decoy 9/9; current-patch revalidation/fallback is exact | wrong-target pointer effect is forbidden, not a finite recoverable cost; 50/50 workload authored; localization pixels are not commensurate with failure utility |
| #575 → #615 | fixed MAP01 visual guard separates coast/recovery; safe reanchor avoids a redundant recapture | `c_g` not isolated; case mix authored; handoff-ready time is not full planner yield cost; stale action never executes so counterfactual `c_f` is unobserved |

## Formal result

- families inspected: **5**
- fully admissible routes: **0**
- authored/not-estimated `p`: **5/5**
- hard-safety/outside-selector `c_f`: **2/5**
- non-selector-ready fields by family count:
  - `c_g`: **3/5**
  - `p`: **5/5**
  - `c_y_stale`: **5/5**
  - `c_y_fresh`: **5/5**
  - `c_f`: **5/5**
  - `s`: **0/5**
  - `f`: **0/5**

The result therefore does not justify plugging values from unrelated experiments into #1646.

## Important distinction

A preregistered 50/50 stale/fresh schedule is useful for testing a mechanism but is **not** an estimate of deployment stale probability.

Likewise:

- local invalidation-to-stop latency is not automatically planner replan cost;
- skipped recapture time is not stale-action failure cost;
- deterministic pixel inspections are not automatically commensurate with wall-time/task-loss utility;
- a wrong-target effect cannot be assigned a convenient finite recovery cost when the underlying contract forbids that effect.

## Preformal retained audit defect

Before source freeze, the first corruption-control pass detected only5/6 mutations. It failed to reject a source-invalid relabeling of the #659/#663 pixel-work proxy as `wall_ms`.

Formal remained0. The repair changed only source-provenance constraints in the auditor; ledger/H/T/D/C/U were unchanged. Construction then rejected6/6 corruption controls. This defect is retained in `PREFORMAL_AUDIT_FAILURE.json`.

## Integrity

The frozen scientific bundle contains PLAN, normalized ledger, analyzer, primary auditor and independent auditor.

- binary Git blob: `23f1666a50b66d2730d6efd1ba8181e31c52b7b7`
- bundle SHA-256: `6e1ac59e9f8ab49728693a7ed496d316cb35da27365e81e613f4dbd135521227`
- branch-retained Base64 Git blob: `978cab535001b5a92b3dbea91f6fa52d6dc62e27`
- ledger semantic digest used by analyzer: `828a6263d6c670c84e761cb4607c0e0c0a029facbcfe7c7e3d772cabc53d654a`
- formal result SHA-256: `411c662e88ff5e7928ae0a5425a32ce8c8a1ed48519cd947ffedb39d88630a7e`
- primary audit: PASS, corruption6/6
- independent audit: PASS, admissible routes0

## Interpretation

#1646 solved the selector mathematics. #1672 shows that the current bottleneck is **parameter identification**, not another guard mechanism.

The retained corpus is strongest on guard mechanics (`c_g,s,f`) and weakest on the quantities needed to value recoverable mistakes: empirical stale incidence and full consequence/recovery costs.

## Next legal rung

Do not create a larger guard mechanism experiment.

Choose one explicitly **recoverable** route and measure the smallest missing set in the same population:

1. passive/independent stale-at-admission incidence `p`;
2. true reject → useful replanning completion cost `c_y_stale`;
3. fresh false-reject → recovery cost `c_y_fresh`;
4. stale action → independently verified failure+recovery cost `c_f`;
5. reuse or remeasure `c_g,s,f` only inside that same route contract.

If executing a stale action would violate a hard correctness contract, that route is not eligible for finite-cost calibration and remains mandatory-pre-guard by #1646's safety override.

No production threshold or route choice follows from this audit alone.
