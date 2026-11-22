# Current-main supported-host acceptance prefix R02

Status: `HOLD_SETUP_OPT_IN_REQUIRED`; this is not a Research Preview acceptance pass.

- Frozen source: main `10b47b4b4edf283ed2b28f19bbeb9de4b9cf9b51`.
- Host: Ubuntu WSL2, Linux `6.18.58.1-microsoft-standard-WSL2`, Python `3.12.3`.
- The official current-main acceptance runner's static launcher preflight passed **19/19** checks, including committed source bytes and executable modes.
- The runner then invoked `./runtime/setup-golden-demo-v3.sh` without `--install-dependencies`. No `runtime/.venv` existed. Setup refused with exit 2 and printed its explicit opt-in instructions; no dependency installation ran.
- The runner stopped before `doctor` and `audit-retained`. `--live` was not requested; no GUI, model call, allocation, or task action occurred.
- Raw conditions, command, step stdout/stderr/exit codes, and aggregate runner JSON are retained here and covered by `SHA256SUMS.txt`.

This rechecks the current-main launcher and explicit setup guard only. Supported-host doctor, retained audit, one fresh no-retry run, and `audit-live` remain unverified; keep Issue #58 open.
