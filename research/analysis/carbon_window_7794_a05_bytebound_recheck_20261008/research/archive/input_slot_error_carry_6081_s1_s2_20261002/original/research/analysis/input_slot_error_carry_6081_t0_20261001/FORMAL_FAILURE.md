# FORMAL FAILURE — runner argument binding STOP

Allocation `INTENT-SLOT-6081-T0-20261001-01`; source freeze commit `176cb87684484de3a134bd09abb0453be1db9163`; base `6cd70ad4bfad74e11658057bf024918bffb24add`.

**Disposition: `STOP_RUNNER_ARGUMENT_BINDING / NOT_EVALUATED`.** The frozen candidate and independent auditor scripts were not run. Each wrapper process launched Python with an empty argument vector and entered the interactive interpreter; both interpreter processes exited 0, but no output file was produced. Thus formal candidate CLI invocations = 0 and formal audit CLI invocations = 0. Host wrapper attempts = 1 candidate-side and 1 audit-side. The apparent exit 0 is not a PASS.

## Exact evidence

- Candidate wrapper start/end: `2026-10-01T13:48:40.9853158Z` / `2026-10-01T13:48:41.5989296Z`; actual argv `[]`; exit 0; stdout empty; stderr is Python 3.12.10 interactive banner/prompt. Captured 176 bytes; SHA-256 `466BCEF12C210BC990BEAD6B20149B5AD3F47FF36C2011B2D02A250173FA12E4`.
- Auditor wrapper start/end: `2026-10-01T13:48:41.6188581Z` / `2026-10-01T13:48:42.0587132Z`; actual argv `[]`; exit 0; same interactive banner/prompt and hash. No `audit.py` execution occurred.
- Both stdout files are empty, SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
- `formal/process_receipts.json`: SHA-256 `C41FABFB17B5273B21C314D4D618B8E9730C09FD99B5A0E709A988AB01833018`.
- `formal/candidate.json` and `formal/audit.json` do not exist. No scientific output was evaluated.

## Cause and containment

The local PowerShell helper declared its argument-array parameter as `$args`, which collides with PowerShell's automatic `$args` variable. The `ProcessStartInfo.ArgumentList` therefore remained empty. This is a harness/runner defect, not a candidate, auditor, or method failure. The wrapper then attempted to display a nonexistent audit report and returned nonzero at the outer-shell level; that shell status is not either Python process's exit status.

No retry, patched replay, or reuse of this consumed allocation is permitted. The frozen source, input, and hashes remain unchanged. A corrected invocation, if justified, requires a separately registered successor allocation with a distinct ID/path/freeze and fresh preflight. Docker was not used; this STOP occurred in the host runner before any scientific CLI or container action.
