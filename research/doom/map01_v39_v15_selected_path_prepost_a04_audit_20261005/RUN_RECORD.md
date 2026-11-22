# A04 run record — terminal auditor implementation failure

- Allocation: `V39-V15-PREPOST-A04-TRACE-AUDIT-20261005-01`
- Candidate/runtime invocations: 0
- Auditor invocations: 1
- Retries: 0
- Auditor source SHA-256: `f433ce309810672555fb7c4f4fbefd02ee98f6a5657a8ba3b0acd08b9755b6e8`
- Runtime: WSLc; image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; network disabled; one CPU
- Observed main at formal launch: `2d8eaaa7758ac180fc2cc3a2a3ee2dcb063f4621` (context only; not the frozen evidence source)
- Formal launch UTC: `2026-10-05T08:52:28.2799526Z`
- Formal exit UTC: `2026-10-05T08:52:29.2414507Z`
- Container exit: 1

The frozen auditor raised `NameError: name 'pre_run' is not defined` while constructing its input digest map. It terminated before parsing inputs or evaluating any baseline/mutation checks. The output directory contains an empty stdout file, the complete Python traceback in `formal/run1/AUDIT_V3.stderr`, and no auditor result JSON. Disposition is `FAIL_AUDITOR_RUNTIME_ERROR_NOT_EVALUATED`; this is not a scientific result and does not invalidate or change A02/A03 history.

The construction suite passed 7/7, and a separate WSLc read-only mount preflight verified the frozen parent-input hashes, A04 freeze JSON, and auditor source. The formal role was not retried. Any corrected audit must use a new version and allocation; the candidate remains uninvoked.
