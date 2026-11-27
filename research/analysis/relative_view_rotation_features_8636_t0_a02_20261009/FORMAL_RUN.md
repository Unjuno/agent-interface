# Formal invocation record — Issue #8636 T0 A02

- Allocation: `UNJUNO-8636-ROTATION-FEATURES-T0-A02-20261009`
- Freeze: `7d92333b35e4acb09d941928413db7a50581cd2a`
- Current-main base: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`
- Platform: Python 3.14.5; Darwin 27.0.0; arm64.
- Execution: local single-process host CPU; no container, GPU, model, GUI, OS input, human, or external service.

| Program | Exact command | Invocations | Exit | Start UTC | End UTC | First output |
|---|---|---:|---:|---|---|---|
| Candidate | `python3 -B runner.py --output results/a02-outcome` | 1/1 | 0 | 2026-10-08T20:52:31Z | 2026-10-08T20:52:43Z | 360 trials; stdout retained |
| Independent auditor | `python3 -B auditor.py --output results/a02-outcome --result results/a02-outcome/audit.json` | 1/1 | 1 | 2026-10-08T20:53:17Z | 2026-10-08T20:53:18Z | `ValueError: status does not match independent decision`; no audit summary written |

Retries: 0. Preserve the exact first output; no formal candidate or auditor command is rerun. Candidate output archive contains 2,216 files / 63,085,782 bytes before compression. Compressed archive is 423,004 bytes and SHA-256 verified against every extracted file.
