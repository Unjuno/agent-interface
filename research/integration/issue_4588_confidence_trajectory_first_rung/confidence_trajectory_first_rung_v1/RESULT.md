# Issue #4588 synthetic first rung — retained integrity failure

## H — Hypotheses

The preregistration hypothesized that confidence velocity/acceleration can
separate otherwise aliased synthetic decisions, and that confidence noise may
make acceleration harmful. It also explicitly required common inputs, timing,
and labels across arms and no outcome-driven retries.

## T — Executed test

The frozen v1 source generated 16 scenario templates × 128 replicates under
clean, ±0.01 and ±0.12 confidence noise; it compared CURRENT_ONLY,
LEVEL_VELOCITY, LEVEL_VELOCITY_ACCEL and causal-EWMA SMOOTHED rules. Seed
20260927. Docker Desktop ran the source once with `--network none`, read-only
source/root, 1 CPU, 256 MiB RAM, 32 PID limit, no capabilities and a bounded
tmpfs. Cached image: `python:3.12-slim`, image ID
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.

## D — Result

**`FAIL_INTEGRITY` — not a valid paired temporal comparison.** The output's
contract assertions passed, but post-run source audit found that `dts` are
drawn inside the scenario loop. Different scenario rows therefore receive
different irregular intervals, despite the source comment claiming matched
timing. In particular, second-order alias pairs were not guaranteed to share
the time intervals needed to isolate acceleration. The internal alias
assertion only evaluated a separate unit example at `(1.0, 1.0)` and did not
verify the generated corpus or per-pair decisions.

The observed aggregate metrics are retained as descriptive output only, not as
evidence for H1/H2/H3/H4:

| condition | arm | accuracy | false executable rate | action recall | correct NO_OP rate |
|---|---|---:|---:|---:|---:|
| clean | CURRENT_ONLY | 62.50% | 33.33% | 75.00% | 0.00% |
| clean | LEVEL_VELOCITY | 93.75% | 8.33% | 100.00% | 75.00% |
| clean | LEVEL_VELOCITY_ACCEL | 89.31% | 0.00% | 57.23% | 100.00% |
| clean | SMOOTHED | 80.86% | 0.00% | 44.53% | 100.00% |
| mild noise | CURRENT_ONLY | 62.50% | 33.33% | 75.00% | 0.00% |
| mild noise | LEVEL_VELOCITY | 93.55% | 8.33% | 99.22% | 75.00% |
| mild noise | LEVEL_VELOCITY_ACCEL | 89.31% | 0.39% | 58.40% | 98.83% |
| mild noise | SMOOTHED | 79.64% | 0.00% | 36.72% | 100.00% |
| stress noise | CURRENT_ONLY | 59.23% | 27.67% | 53.13% | 24.41% |
| stress noise | LEVEL_VELOCITY | 72.07% | 6.90% | 47.27% | 43.55% |
| stress noise | LEVEL_VELOCITY_ACCEL | 68.65% | 3.52% | 23.44% | 52.73% |
| stress noise | SMOOTHED | 66.02% | 3.39% | 13.48% | 76.95% |

All rows had `n=2048`; noise-specific observations remain as printed by the
single retained Docker invocation. The exact invocation output showed
`contract_controls=PASS`, `model_trained=false`, and `authority_granted=false`.

## C — Controls and provenance

- Preregistration SHA-256:
  `85f7a9309368b7c256b259eba7ef84b1067b87e1ed1541f56adf914f39719153`.
- Frozen script SHA-256:
  `5b7433c9ac30d3cfba0861a9c1720856019d665581084c5b4635c3280245192f`.
- The four arms used the same rows within each run; however, scenario-pair
  timing was not matched. No outcomes were used to tune or rerun v1.
- A separate v2 is warranted only to repair this design flaw. v1 source and
  this disposition are immutable and must not be relabeled as a pass.

## U — Limits / stop

Do not infer that temporal features help or hurt from these aggregate results.
This run does not satisfy the issue's matched temporal-corpus comparison, and
it does not establish model calibration, real caller-visible histories, GUI
correctness, shadow/live safety, human tempo, or efficiency benefit. Stop v1;
any follow-up is a distinct allocation with common scenario clocks/noise and a
new source hash.
