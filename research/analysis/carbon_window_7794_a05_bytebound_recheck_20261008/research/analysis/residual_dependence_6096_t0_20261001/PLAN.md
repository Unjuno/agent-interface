# Issue #6096 T0 — subthreshold residual dependence sentinel

## Scope and target claim

Offline finite-sequence method test only. The question is whether a fixed-lag signed-residual dependence sentinel can stop an already authorized continuation before a separately scored wrong continuation, at a frozen zero false-YIELD limit on valid controls. It cannot extend or create input authority. No GUI, model, game, physical input, or runtime effect is in scope.

## H / T / D / C / U

- **H:** A dependence sentinel detects at least one held-out zero-mean, pointwise-subthreshold residual process before its first wrong continuation, while not stopping valid periodic-motion/jitter controls under the same residual-only evidence; pointwise and running-mean baselines miss the danger case.
- **T:** Freeze a training-only threshold rule and exact integer residual traces. Residual units are quarters. Pointwise threshold is 1/2; running signed-mean threshold is 1/5. The dependence statistic is the sum of the last five adjacent signed residual products; calibrate the trigger threshold to one plus the maximum such statistic in training controls, giving zero training false alarms. Compare pointwise, running-mean, calibrated dependence, fixed-short-hold (stop after four observations), and always-YIELD. Test held-out subthreshold phase-lag danger, matching valid periodic motion and camera-jitter sequences, independent low-amplitude noise, a mean-shift positive control, target identity change, and missing evidence. The independent oracle holds wrong-continuation and harmlessness labels.
- **D:** `PASS_METHOD_SCOPED` only if the calibrated dependence sentinel stops by the last safe observation before the first wrong continuation, has zero false stops on held-out valid periodic/jitter controls, and all source/missing-evidence invalidations fail closed. `FAIL_METHOD` if matched valid controls force the calibrated threshold above the danger trace or if the sentinel alarms harmless periodic residuals; `STOP` for any provenance or reconstruction defect. No statistical p-value or GUI safety claim.
- **C:** A residual-only statistic may be observationally unable to distinguish harmful phase lag from harmless animation/camera jitter with the same prefix. A source-bound mode/hazard cue or simpler fixed hold may be required. The finite control family is deliberately explicit and does not tune a textbook Ljung–Box test.
- **U:** No short-sample false-alarm guarantee, adaptive-sampling correction, real actuator calibration, target semantics, collision outcome, or transfer to application/game safety. Equal residual histories can have different latent outcomes; the test addresses only the frozen sequences and decision time.

## Freeze and execution controls

Before formal execution: run construction tests, freeze all source/public/truth hashes, and verify the candidate cannot read truth labels. Candidate invocation maximum 1; independent auditor maximum 1; retries 0. Keep construction failures and any launch errors in `RUN.json`. Docker is preferred, but the Docker Desktop Engine was unavailable at intake; no shared service start is authorized while #5085 ownership remains unresolved. If still unavailable, execute this pure finite CPU fixture on the host and disclose the deviation.
