# Issue #3312 — support-complete A3 guard calibration result

## Disposition

**PASS_SUPPORT_COMPLETE_CALIBRATION_AUDITED** for the narrow #3312 support-evidence gate.

This does **not** rewrite #2546's historical PASS or #2494's later STOP/HOLD. It supplies a fresh, episode-disjoint support-complete allocation on the inherited #2546/A3 private-X11 route. It is not a production guard-policy recommendation.

Formal allocation: `guard-support-complete-3312-20260923-01`  
Base main: `2aac474ff82b5f8b1a90708850a39bb853ee19c2`  
Formal invocations/reruns/replacements/tuning: **1 / 0 / 0 / 0**  
Execution exit: **0**; wall receipt: **9.509477035 s**.

## H/T/D/C/U

### H
The retained A3 route can prospectively allocate and retain non-zero same-route support for every #3312 support stratum without pooling historical rows or leaking fixture truth to the selector.

### T
The exact retained A3 fixture/helper source was reconstructed from current-main retained source parts. Route semantics were held: private Xvfb/Tk/XTEST, cached left target, 32x32 exact ROI guard, 120 ms success horizon, 3 ms stale-no-effect boundary, parent baseline-subtraction cost equations, q tiers, and terminal button-neutrality.

Only the support allocation/audit changed. Formal raw contains:
- 16 calibration blocks x 4 rows = 64 rows;
- 5 held-out support strata x 6 = 30 rows;
- diagnostic q-tier transfer: 4 q tiers x 32 paired episodes x 2 arms = 256 rows;
- total = 350 rows.

Right-censored rows use a fixed 5 ms post-stale-action recovery horizon, intentionally stop before fallback, and are excluded from finite recovery-cost estimates.

### D
Held-out support counts were exactly 6 each:
- `STALE_REFUSAL`: 6
- `FRESH_REFUSAL`: 6
- `STALE_ACTION_RECOVERY`: 6
- `FRESH_SUCCESS`: 6
- `RIGHT_CENSORED`: 6

Calibration/evaluation episode IDs were disjoint. Truth was reconstructed after decisions from fixture reset journals. All rows were terminal button-neutral. Every stale-action recovery had an independently logged initial noop followed by recovery success; every right-censored control retained only the stale noop and no fallback.

Inherited cost equations over 16 complete calibration blocks:

| quantity | mean | 95% paired bootstrap interval | negative samples |
|---|---:|---:|---:|
| `c_y_stale` | 10.261058 ms | [9.930097, 10.759400] ms | 0 |
| `c_y_fresh` | 10.223024 ms | [9.934716, 10.536764] ms | 0 |
| `c_f` | 14.399024 ms | [13.381675, 15.800980] ms | 0 |

The frozen raw-only auditor returned exit0, errors `[]`, and rejected 9/9 semantic corruptions.

The frozen auditor did not aggregate the preregistered diagnostic q-tier rows. This omission was discovered only after formal completion. No scientific case was rerun. A separately versioned, standard-library, read-only postformal audit reconstructed the four tiers from the retained 256 policy rows and rejected 9/9 additional corruptions:

| q | realized stale | predicted | observed paired result |
|---|---:|---|---|
| 1/100 | 1/32 | GUARD | UNKNOWN; CI crosses zero |
| 1/20 | 0/32 | POST | POST |
| 1/5 | 9/32 | GUARD | GUARD |
| 1/2 | 19/32 | GUARD | GUARD |

For this postformal diagnostic only, guard acquisition cost is the mean retained PRE_GUARD `guard_ns` in the policy rows (0.092191 ms), because this allocation did not retain the parent's separate classification-probe sample. This diagnostic does not change the primary #3312 support-completeness decision.

### C
The five support strata were deliberately allocated; their counts are not natural stale incidence. `FRESH_REFUSAL` is a forced policy control, not a measured natural false-reject rate. The censor horizon is authored. The fixture is one synthetic private-X11 route.

### U
No universal guard economics, model/token benefit, end-to-end task speed, natural stale probability, cross-application transfer, human-tempo result, production policy, or #2789 integrated acceptance follows.

## Preserved construction/publication incidents

Before formal0:
1. a unittest invocation used an import-incompatible absolute file form and stopped before tests;
2. the first corrected synthetic audit exposed that the `lost_recovery` corruption was not rejected;
3. the auditor was strengthened, synthetic tests passed 2/2 and 9/9 controls rejected;
4. an excluded five-stratum private-X11 seam passed with all neutral endpoints and fixture exit0;
5. the first GitHub JSON publication used semantically equivalent but byte-different formatting for four freeze files. Remote readback detected the mismatch at formal0; exact local bytes were then published and re-read before formal execution.

None of these construction/publication rows contributes to formal estimates.

## Integrity

Frozen source hashes were unchanged after formal execution.

- `RESULT.json` SHA-256: `2107e2d37171bd026a8e2e2314643bd1d94bb23816799a4bb373c5d7ae37a26e`
- frozen `AUDIT.json` SHA-256: `1255cd6a8b3ff6a28805897922572441e1cdfa93eef5e7ed42301de493677560`
- postformal `AUDIT_V2.json` SHA-256: `0aa78a019e994ca9e9c8454bd2d89983b07cdbc4ae9f79092aa92e95126c5474`
- `FREEZE.json` SHA-256: `7b912af369619d6019f50f2350cae768e916f8fc0399aa7c82bdd0a59069598a`

No owned Xvfb/fixture process remained after execution. Docker CLI/image attestation was unavailable: actual environment is the provided Linux x86_64 execution container, CPython 3.13.5, Tk 8.6, python-xlib 0.15, Xvfb package `2:21.1.16-1.3+deb13u1`.
