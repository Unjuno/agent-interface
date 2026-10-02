# A01 run record — quantized upper-tail counterexample

**Disposition: `COUNTEREXAMPLE_A01`.** Candidate 1/1 exit 0; independent raw-only auditor 1/1 exit 0 (`AUDIT_VALID`); retries 0.

## Executed allocation

- Frozen allocation: `6576-TIMER-QUANTIZATION-A01-20261002`; frozen main `dbf0056e96ae1a3b04fe426cb86501442661a1b8`.
- OrbStack machine: `agent-interface-6576-tailid-parity-a03-20261002`, ID `01M3Y3Z0A534XSFW13KW95E98Y`, Ubuntu 24.04 arm64. Its private Docker Engine had no running containers before launch. The shared `unjuno-native-ci-6092` Engine/container was not used or touched.
- Image: `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (linux/arm64).
- Candidate container ID: `e1cdcfd513602f2130f7bb9ac2fc1c590aa6e70e383162249c2da911bd4c9226`; auditor ID: `06cb47261d14944a60a3a5a621d916aa52686f343d09ddd3fa2570641b99193e`.
- Both containers used network none, read-only root, 1 CPU, 2 GiB RAM, 2 GiB memory+swap (zero swap), `/tmp` tmpfs 64 MiB noexec/nosuid. Candidate source/input were read-only and only its separate output mount writable. Auditor source/input/candidate result were read-only and only its separate audit output mount writable. Both configs were inspected while `created` before start.
- Candidate command: `python /src/candidate.py /src/input.json /out/result.json`.
- Auditor command: `python /src/audit.py /input/input.json /candidate/result.json`.
- Candidate/auditor exit receipts are retained; stdout and stderr are empty for the candidate, while auditor stdout contains `AUDIT_VALID` and all three independently recomputed rows.

## Results

| Arm | Gate decision | Training exceedances above observed q90 | Distinct exceedance values | Largest tied bin |
|---|---:|---:|---:|---:|
| Continuous, q=0 | `NOT_ESTIMABLE_DIAGNOSTIC_GATE` | 400 | 400 | 1 |
| Rounded, q=0.25 | `ELIGIBLE_REFERENCE` | 357 | 21 | 89 |
| Rounded, q=1.0 | `ELIGIBLE_REFERENCE` | 333 | 6 | 212 |

The continuous arm failed the existing block-median ratio criterion at 1.54513 (>1.5); its lag-1 threshold-indicator correlation was effectively zero. The q=0.25 arm passed at ratio 1.5 and correlation -0.01470. The q=1.0 arm passed at ratio 1.0 and correlation 0.00744. The q=1.0 arm satisfies the preregistered counterexample: current diagnostics accept it as `ELIGIBLE_REFERENCE` despite only six distinct observed values in 333 threshold exceedances.

Descriptive holdout counts above the training observed q90 threshold were 1,040/10,000 latent and observed for the continuous arm, 1,057 latent versus 950 rounded observed at q=0.25, and 1,367 latent versus 821 rounded observed at q=1.0. These are threshold exceedances, not p99 predictions or calibration scores; the discrete and latent endpoints differ by design.

## Interpretation and scope

This is one deterministic synthetic counterexample to completeness of the current eligibility diagnostics: timer quantization/tied support is not represented, and a coarse quantized arm can pass the existing gate. It does **not** show that any EVT/TailID fit is inaccurate, that a fitted p99 is miscalibrated, that quantized values cannot be modeled, or that a real platform has the tested resolution. No EVT/GPD fit was run. No real release endpoint, physical key-up, operational timer, safety deadline, protection property, worst-case bound, or population behavior was measured. The continuous control's unrelated stability rejection also limits any between-arm causal interpretation.

The six-case formal #6576 T0 remains a separate allocation and was not invoked. No previously consumed allocation was retried. The source, frozen input, raw candidate result, auditor output, and exits are retained under this directory; hashes are in `SHA256SUMS`.

## Local validation

The focused existing #6576 construction suite passed 24/24 via `python3 -m unittest discover -s research/analysis/extreme_tail_eligibility_6576_construction_v1 -p 'test_*.py' -v`; candidate/auditor/generator `py_compile` and `git diff --check` passed. An initial test command launched from inside the nested experiment directory failed at test-module import (`ModuleNotFoundError: research`) before executing any tests; no test result was produced by that invocation, and the repository-root discovery run above is the successful validation.
