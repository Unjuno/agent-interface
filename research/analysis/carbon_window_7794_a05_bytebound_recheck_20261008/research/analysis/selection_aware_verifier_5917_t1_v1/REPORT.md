# Issue #5917 T1-01 result

Allocation `VERIFIER-SELECTION-5917-T1-LOCALCPU-20261001-01`; frozen base main `4b7fe7837e4ee8c0d035ebfbf52baf014f042295`; additive branch `research/selection-aware-verifier-5917-t1-20261001`.

## Result

**`PASS_METHOD_SCOPED`**. Candidate process exit 0; separate raw-only auditor exit 0; 256/256 feasible positive-support selection assignments enumerated; exact probability mass 1; auditor matched every candidate assignment and rejected all 3/3 frozen mutations.

| Estimator (per verifier) | Exact finite-population mean | Bias | Exact draw-distribution MSE | Notes |
|---|---:|---:|---:|---|
| Census truth | 0.500000 | — | — | Both A and B |
| Selected-only, conditional on any selection | 0.915890 | +0.415890 | 0.188004 | Undefined mass 0.00006561 retained separately |
| Horvitz–Thompson (known p) | 0.500000 | 0 | 0.006944 | Not clipped; max inverse weight 10 |
| DR: correct p, misspecified q=.25 | 0.500000 | 0 | 0.039063 | Unbiased in exact expectation; retains higher variance than HT |
| DR: wrong p=.5, exact q | 0.500000 | 0 | 0 | Correct outcome model makes this fixture exact |
| DR: both wrong (p=.5, q=.25) | 0.900000 | +0.400000 | 0.174063 | Does not receive a “doubly robust” pass |

A and B have the same metrics by the symmetric frozen fixture. For the selected-only estimator, the conditional mean/bias/MSE are over draws with at least one observation; the probability of an undefined no-selection draw is reported and not imputed. Quantiles in `AUDIT.json` are exact randomization-distribution quantiles, not confidence intervals. Mean Kish ESS was 3.06124 (minimum positive 1). Expected A-selection calibration error was 0 in all four family × difficulty cells.

**Zero-support control:** 16 feasible assignments. Two worlds differing only in B's never-selected hard-row outcomes generate identical observed logs, while B's census accuracy changes from 0.5 to 0.0. The output correctly refuses the population mean as `NONIDENTIFIABLE_FROM_LOGS`.

## H / T / D / C / U interpretation

- **H:** Supported within this frozen synthetic fixture. Selection-only estimates were biased; known-propensity HT / one-correct-component DR were unbiased across the complete draw distribution; both-wrong DR remained biased.
- **T:** Exactly the frozen eight-row, two-family fixture and estimators. Candidate once and independent auditor once, each as a separate local Windows Python process. Raw candidate stdout is preserved exactly in compressed/Base64 form; raw auditor stdout is `AUDIT.json`.
- **D:** All preregistered method gates passed, including 256-row exact enumeration, calibration, weight/ESS diagnostics, positivity refusal, equivalent zero-support logs, and 3/3 mutation rejection.
- **C:** Deterministic outcomes, exact known propensities, strong engineered correlation and eight cases. This deliberately idealized fixture is not natural logging data.
- **U:** No empirical verifier competence, real route/policy value, task-quality, T2 shadow-interference, safety, or production claim. No T2 shadow check is authorized by this T1 result.

## Execution boundary

The experiment used local CPU only; this arithmetic method has no reason to consume the idle RTX 3080. Docker was not invoked because the host Docker CLI/inventory was unresponsive; the local method test requires only stdlib and ran with no persistent local output writes. This is a disclosed host-CPU execution deviation, not a container reproduction. No cloud/remote experiment, model load, CUDA, GUI/input, or network call was made by either experiment process.

Reproduction from this directory (stdlib only; preserves separate candidate/auditor processes):

```python
import json, subprocess, sys
fixture = json.load(open("fixture.json", encoding="utf-8"))
candidate = subprocess.run(
    [sys.executable, "candidate.py"],
    input=json.dumps(fixture, separators=(",", ":")).encode(),
    stdout=subprocess.PIPE, check=True,
)
bundle = json.dumps(
    {"fixture": fixture, "candidate": json.loads(candidate.stdout)},
    separators=(",", ":"),
).encode()
subprocess.run([sys.executable, "audit.py"], input=bundle, check=True)
```

The independent auditor imports no candidate implementation.
