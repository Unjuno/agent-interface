# Formal invocation receipt — UNJUNO-8636-ROTATION-FEATURES-T0-A01-20261009

Freeze commit: `2e8f1d5bca6f` (source freeze and protocol; base `a5f53b6ef1810b74b5539dc0048e43b128b4cb7b`). Preregistration was posted to Issue #8636 before these invocations. This is the sole formal candidate call and sole formal auditor call for this allocation.

| Invocation | Command | Exit | First outcome |
|---|---|---:|---|
| Candidate | `python3 -B runner.py --output results/first-outcome` | 0 | 360 trials, 2,199 observation events, 360 terminal neutral release receipts |
| Independent auditor | `python3 -B auditor.py --output results/first-outcome --result results/first-outcome/audit.json` | 1 | First mismatch: `focal_shift-30011-raw_pixels`, step 0, YIELD / `feature shape changed`; raised `ValueError: status does not match independent decision`; no `audit.json` was written |

The runner produced 2,202 files (about 63 MiB unpacked). `results/first-outcome.tar.gz` retains the exact first output. No formal program was rerun, and no output was tuned or replaced. The 63 YIELD observations remain unaudited; this count is descriptive only.

The issue is the frozen decision contract: feature-shape rejection is expected in the explicit invalid-feature stratum, but focal shift is treated as a separate stress stratum. The raw-pixel controller hit the same frozen shape-integrity gate on a focal-shift frame, and the auditor's `expected_fault_yield()` classifies this YIELD as unexpected. The audit therefore halted at its first such event; this report makes no claims about later rows or the experiment hypothesis. A corrected auditor cannot retroactively upgrade this first outcome; it requires a new allocation, freeze, and run.

## Retained artifact SHA-256

- `results/first-outcome.tar.gz`: `e85c70e879f16e57bade77f6a52b05cd75c85385ab40e3d3394b76a96753096d`
- `results/runner.stdout.txt`: `30f396528744988a67763d2a33dba148247d18004d5f3a1091a1c92c34a1dc6c`
- `results/runner.exit_code.txt`: `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- `results/auditor.stdout.txt`: `34e3c43586302371732ee1acffbbaf6e8e7a0f6d672b83700041e58b85cb3a8f`
- `results/auditor.exit_code.txt`: `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`
