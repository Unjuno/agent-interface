# Issue #5322 formal-01 result

## H / T / D / C / U

- **H:** In this synthetic one-shot incentive simulator, proper scoring plus randomized audits reduces responsive overclaiming while preserving calibration, false-PASS, valid-UNKNOWN, and audit-cost constraints; the adversarial audit should detect at least 30% of false-independence declarations.
- **T:** One preregistered invocation on GitHub Actions run [36699576828](https://github.com/Unjuno/agent-interface/actions/runs/36699576828), from frozen trigger commit `60b26d062c8667d3bfe3608c372c9e3d62ebcaab`. No retries. Container was `python:3.12-slim`, Python 3.12.14, Linux x86_64. Construction tests passed. The simulator emitted 6,720 tasks and 33,600 policy rows across the preregistered five arms.
- **D:** **FAIL (4/6 numerical gates passed).** Independent raw audit status PASS, zero errors, all five frozen corruption controls rejected. Raw SHA-256 is `299fe4403f27309c2915cad9a7449d1b496cffb2b5b6a8fd950d9f90433dad5c`; independently recomputed from the published raw file, which contains exactly 33,600 JSONL records.
- **C:** Results are the synthetic simulator only. They do not validate a model, runtime agent, real incentive, production authority, or deployment.
- **U:** The outcome is scoped to these fixed synthetic assumptions, strategies, seeds and thresholds. The separately preregistered GPU model pilot was not allocated or run.

## Decision gates

| Gate | Frozen threshold | Observed | Result |
|---|---:|---:|---|
| Responsive overclaim reduction vs metadata-only | >= 0.15 | 0.259970 | PASS |
| Responsive Brier delta vs metadata-only | <= 0 | -0.001184 | PASS |
| False-PASS increase vs metadata-only | <= 0.01 | -0.004167 | PASS |
| Valid-UNKNOWN change vs metadata-only | >= -0.02 | -0.116518 | FAIL |
| Mean audits per agent slot | <= 0.25 | 0.192150 | PASS |
| False-independence detection | >= 0.30 | 0.250000 | FAIL |

The mechanism's main tradeoff is visible in the paired outcomes: it eliminates responsive overclaiming in this synthetic setting, but also suppresses valid UNKNOWN reporting far beyond the allowed tolerance. The adversarial audit misses the preregistered detection target. These failures must remain visible; do not reinterpret the aggregate PASS count as an overall PASS.

## Authoritative artifacts

- [Frozen source manifest](FREEZE.json)
- [Preregistration](PREREGISTRATION.md)
- [Machine decision](results/formal-01/DECISION.json)
- [Independent raw audit](results/formal-01/AUDIT.json)
- [Aggregate summary](results/formal-01/summary.json)
- [Raw JSONL](results/formal-01/raw.jsonl)
- [Environment](results/environment.json)
- [Workflow run](https://github.com/Unjuno/agent-interface/actions/runs/36699576828)

The initial `STOP.md` records a pre-allocation source-readback concern. That concern was resolved by re-reading GitHub Contents as base64 and confirming exact byte hashes against the original manifest before creating the one-shot trigger. The subsequent formal run is the sole allocation; the STOP history is preserved, not treated as the formal result.
