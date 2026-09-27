# #3847 Needle pilot-05 — formal report

**Disposition: `FAIL_NEAR_BOUNDARY_SHIFT`** (scoped). The preregistered hybrid Needle did not preserve intent labels on an in-envelope near-boundary covariate shift. The one formal training/evaluation invocation completed once on local Docker CPU; there was no retraining, tuning, seed substitution, or retry.

## Result

The independent corrected auditor found zero raw-row, source-weight, teacher-label, prediction-reconstruction, or yield-integrity errors. It recomputed the retained raw bytes (`FORMAL_RESULT.json`, SHA-256 `39577a8750441f6b25c506d8dcc4bf74d6c696cfcd988a2d291dc7be0a95d901`). The audit's `FAIL_OR_HOLD_NEAR_BOUNDARY_SHIFT` umbrella disposition is a **FAIL**, not HOLD: the audit completed with `errors: []`, and the numerical preregistered quality gates were missed.

| Seed | Shift accepted accuracy | CONTINUE coverage / recall | CORRECT coverage / recall | WATCH coverage / recall | False CORRECT / accepted | CPU p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| 3464 | 0.7309 | 0.9092 / 1.000 | 0.7910 / 0.2790 | 0.4229 / 0.9977 | 0 / 2,174 (0%) | 0.0369 |
| 3465 | 0.7660 | 0.8887 / 1.000 | 0.7900 / 0.4227 | 0.4209 / 0.9165 | 0 / 2,150 (0%) | 0.0398 |
| 3466 | 0.6886 | 0.8770 / 1.000 | 0.8223 / 0.2708 | 0.4238 / 0.8548 | 16 / 2,174 (0.736%) | 0.0440 |

Required shifted accuracy was >=0.95, each class coverage >=0.75, each accepted per-class recall >=0.95, false CORRECT <=0.5%, CPU p95 <60 ms. All three seeds fail quality: CORRECT recall is 0.271–0.423; WATCH coverage is 0.421–0.424; WATCH recall also misses in seeds 3465/3466; seed 3466 exceeds false-CORRECT cap. Latency passes. Every seed yielded on all 1,536/1,536 explicit boundary cases and all five invalid metadata/envelope/nonfinite controls.

The matched IID control accuracy was 0.9985, 0.9969, and 0.9939. This does not rescue the shifted failure; it isolates the issue to distribution shift rather than inability to fit the training-like generator. IID is diagnostic-only by preregistration.

## Audit-tool STOP

The first auditor invocation stopped before writing an audit because the frozen auditor's `summarize()` return block was misplaced (`TypeError: 'NoneType' object is not subscriptable`). This is preserved in `audit/AUDIT_ATTEMPT_01_STOP.json`; it is not a model FAIL. The runner, formal output, freeze, and thresholds were not changed. The auditor source alone was corrected and run against the same immutable raw result; the successful independent audit is `audit/AUDIT.json` and its source correction is described in `audit/AUDIT_SOURCE_CORRECTION.md`. The frozen auditor remains recoverable at source commit `00e3de66f196bcc8dd0ca54a5eb08f40c989c32c` and is hash-pinned in `FREEZE.json`.

## H / T / D / C / U

- **H:** Falsified for this declared distribution. The frozen margin-plus-student approach did not retain useful CORRECT/WATCH recall/coverage near the decision boundary.
- **T:** Fresh seeds 3464–3466; exact pilot-04 model/training settings; balanced IID plus shifted 1,024/class and fixed boundary suite; one local Docker CPU invocation. Full rows, model weights, latency vectors and seed data are retained.
- **D:** FAIL. Shift accuracy/coverage/recall/correct-proposal gates miss as tabulated. Boundary/invalid YIELD and latency gates pass. Independent audit errors: zero.
- **C:** Synthetic teacher only, no external inference, GUI/input, action/effect, or model authority. Only deterministic guards can YIELD/allow a local proposal; no proposal was executed.
- **U:** This is not Astra-labeled, visual, GUI/servo, task-effect, multi-task transfer, production, or runtime-integration evidence. Three seeds do not characterize all covariate shifts.

## Next research implication

Do not expand the fixed threshold margin or retune this allocation. A new successor should use externally authored intent labels or real observation traces and compare the deterministic rule, frozen student, and selective YIELD on a preregistered near-boundary set. Preserve this FAIL unchanged.
