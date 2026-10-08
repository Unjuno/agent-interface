# Needle pilot-06 — formal report

**Disposition: `FAIL_NEAR_BOUNDARY_SHIFT`.** The one-shot local Docker CPU experiment fails the preregistered shifted accuracy and CORRECT recall gates across all three seeds. This conclusion is based on a corrected independent audit with zero evidence errors. No model, training, seed or evaluation rerun occurred during auditor correction.

## Formal result

One network-isolated Docker invocation trained/evaluated seeds 3467, 3468 and 3469. The retained 3,701,595-byte `FORMAL_RESULT.json` has SHA-256 `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`. Full row-level suites, model weights, invalid inputs and latency samples are retained.

| Seed | Shift accepted accuracy | CONTINUE coverage / recall | CORRECT coverage / recall | WATCH coverage / recall | False CORRECT / accepted | CPU p95 ms | IID accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3467 | 0.7412 | 0.882 / 1.000 | 0.821 / 0.187 | 0.890 / 0.997 | 0.113% | 0.0421 | 0.9969 |
| 3468 | 0.7015 | 0.899 / 1.000 | 0.795 / 0.026 | 0.900 / 1.000 | 0.000% | 0.0357 | 0.9947 |
| 3469 | 0.7830 | 0.903 / 1.000 | 0.806 / 0.301 | 0.906 / 0.996 | 0.112% | 0.0386 | 0.9989 |

The frozen gates require shifted accuracy ≥0.95, each class coverage ≥0.75 and recall ≥0.95, false CORRECT ≤0.5%, boundary and invalid controls to yield, and CPU p95 <60ms. Accuracy and CORRECT recall fail on all seeds; the other listed gates pass. All 1,536/1,536 explicit boundary rows per seed yielded. All five serialized invalid probes per seed independently recomputed to the expected yield reason. The IID control is diagnostic only and does not rescue this FAIL.

## Auditor STOP and correction

Initial auditor attempt `AUDIT_ATTEMPT_01_STOP.json` returned 6,156 errors and nonzero status. Root causes were in the auditor only: its independent baseline reconstruction used shape-varying random draws, and invalid float32 values were compared exactly against decimal float64 literals. A first corrected audit output is retained as `AUDIT_CORRECTED.json`; subsequent hardening also made the auditor independently verify each boundary input rather than trusting the reported reason. `AUDIT_SOURCE_CORRECTION.md` documents all changes. `AUDIT_FINAL.json` re-audits the same immutable formal bytes, independently regenerates full-size 1,024-row control arrays, tolerates only 1e-6 input representation error, recomputes boundary reasons, reconstructs model predictions and metrics, and reports `errors: []`. Its top-level gate disposition remains `FAIL_OR_HOLD_NEAR_BOUNDARY_SHIFT`; the numeric gates establish FAIL, not HOLD. All audit attempts are retained.

## H / T / D / C / U

- **H:** Falsified for the declared isolated synthetic near-boundary shift. Correct-only covariate movement still causes severe loss of CORRECT accepted recall, despite unchanged CONTINUE/WATCH controls.
- **T:** Fixed pilot-04 model/gates; seeds 3467–3469; one local network-isolated Docker CPU invocation; three suites, explicit boundaries, invalid controls and 2,000 latency samples per seed.
- **D:** FAIL. Shift accepted accuracy is 0.7015–0.7830 versus ≥0.95, CORRECT recall is 0.026–0.301 versus ≥0.95. Corrected independent audit has zero errors. Latency, other class coverage/recall, false-CORRECT, boundary and invalid-YIELD checks pass.
- **C:** Authority-neutral synthetic proposals only; no GPU, external inference, GUI/input, real action, execution permission, or product/runtime integration.
- **U:** Not Astra intent fidelity, real observations, perception, servo/task effect, production, or general Needle evidence. The shift is a hand-authored synthetic teacher and three seeds.

## Research implication

Do not tune or reinterpret this allocation. The near-boundary weakness reproduced after isolating the class shift, but still only under a synthetic teacher. The next evidence-bearing step is externally authored intent labels or real observation traces with a frozen comparison of rule baseline, student and selective YIELD. Preserve this FAIL and the initial auditor STOP unchanged.
