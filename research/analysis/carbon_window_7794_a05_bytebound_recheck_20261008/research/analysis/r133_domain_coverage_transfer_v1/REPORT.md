# r133 cross-domain evidence coverage transfer — T0-03

## H/T/D/C/U

- **H:** An axis-separated coverage vector can represent physical bounded input brackets, interval-censored continuous-control occupancy, weak state feedback, untimed discrete-task outcomes and observation counts without imputing missing or censored endpoints as zero or success.
- **T:** Reconstruct a deterministic vector from exact retained blobs at base `6968d45197c6a29e717a9281dcd050be1eed90c7` in one network-disabled Docker candidate process; independently reconstruct it in a second container; test directed promotion errors.
- **D:** PASS requires exact independent reconstruction, all four blob SHA-1s verified, no scalar overall score, and rejection of duration, task-effect and v39 precision-gate promotion.
- **C:** Retained evidence summaries only. No GUI/game/model calls, input actuation, raw-trace scan, or repeat of any prior allocation. Cross-domain comparisons are semantic only, not matched performance measurements.
- **U:** Does not measure new held-input duration, first-useful-feedback time, task effect, bounded recovery, human tempo, causal v38/v39 speed, or performance transfer; it does not complete r133.

## Execution record

- **T0-01:** `STOP_CONTAINER_SOURCE_READER_MISSING`; Python image lacked Git. Stopped before reading evidence.
- **T0-02:** `STOP_DOCKER_STDIN_NOT_ATTACHED`; `docker run` lacked `-i`; payload was empty and parsing failed before source verification. Both predecessor outcomes are retained without retry.
- **T0-03:** Candidate and auditor each ran once, in separate `r133-coverage-t0-03:local` containers. The image is Python 3.12.10 slim, base digest `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`, built image ID `sha256:e5d95927cc83ac8086b20505ade306aa1e7ca994efa8c32336eefada4ce7fe12`. Both containers used `--network none`, read-only root, bounded `/tmp`, and only the evidence bundle as writable mount. Host handoff verified commit:path object IDs; each container independently recomputed each incoming Git blob SHA-1.
- **Candidate:** `CANDIDATE_RECONSTRUCTED`; SHA-256 `7a9523ea26de836cb29c76062462c166a9b04b2c1c61644a7d9c73a083079208`.
- **Independent audit:** `PASS`, zero errors. See `results/t0-03/audit.json` and both captured Docker logs.
- **Corruption controls:** 3/3 rejected by separate-process auditor tests: Calc release-only promoted to duration, state-only health/ammo feedback promoted to plan-bound task effect, and v39 precision gate flipped false→true.
- **Construction suite:** 18/18 `unittest` tests passed on the host. This is separate from the one-shot formal Docker reconstruction.

## Evidence vector

| Domain | Occupancy / input | Outcome and feedback |
|---|---|---|
| DOOM physical R1 | Six XTEST-owner actuation edges; max censor width 0.559054 ms; scoped `MEASURED_BOUNDED`, not continuous MAP01 occupancy duration. | No task-effect or useful-feedback timing claim from this source. |
| DOOM v38/v39 retained summaries | Interval-censored: v38 3,048.890–4,039.878 ms, width 990.987 ms, precision gate passed; v39 6,301.200–8,452.733 ms, width 2,151.534 ms, gate failed. | 3/4 plans have state feedback; 0/4 have plan-bound task effects. |
| Calc final wait | Release verified, duration unmeasured. | Saved output verified 4/4 but untimed; two extra observations; first-useful-feedback time unidentifiable. |

No scalar coverage score is emitted. The evidence supports only the scoped claim that these frozen result types can be represented without conflating their axes and that the tested promotions are detected. No claim follows that any domain performs better or transfers to another.

## Retained artifacts

- Freeze: `FREEZE_T0-03.json`; H/T/D/C/U and invocation instructions: `PLAN.md`.
- Candidate, run metadata and independent verdict: `results/t0-03/`.
- Earlier STOP records remain under `results/t0-01/` and `results/t0-02/`.
- `SHA256SUMS.txt` inventories report, code, freeze and raw evidence. No T0-03 input, output or audit was rerun after its one-shot completion.

Issue #12 remains open; this package advances its cross-domain evidence contract but is not the full held-out benchmark/oracle contract or an end-to-end performance evaluation.
