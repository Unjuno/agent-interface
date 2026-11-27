# Current-main supported-host acceptance prefix R02

Status: `HOLD_SETUP_OPT_IN_REQUIRED`; this is not a Research Preview acceptance pass.

- Frozen source: main `10b47b4b4edf283ed2b28f19bbeb9de4b9cf9b51`.
- Host: Ubuntu WSL2, Linux `6.18.58.1-microsoft-standard-WSL2`, Python `3.12.3`.
- The official current-main acceptance runner's static launcher preflight passed **19/19** checks, including committed source bytes and executable modes.
- The runner then invoked `./runtime/setup-golden-demo-v3.sh` without `--install-dependencies`. No `runtime/.venv` existed. Setup refused with exit 2 and printed its explicit opt-in instructions; no dependency installation ran.
- The runner stopped before `doctor` and `audit-retained`. `--live` was not requested; no GUI, model call, allocation, or task action occurred.
- Raw conditions, command, step stdout/stderr/exit codes, and aggregate runner JSON are retained here and covered by `SHA256SUMS.txt`.

This rechecks the current-main launcher and explicit setup guard only. Supported-host doctor, retained audit, one fresh no-retry run, and `audit-live` remain unverified; keep Issue #58 open.

## Supplemental read-only checks (same frozen source)

After the official runner stopped at the explicit dependency-install opt-in gate, two direct read-only checks reused the already-present RC1 WSL venv. Current-main and RC1 `runtime/requirements-golden.txt` were byte-identical (SHA-256 `1065afbce7e148dfb1a736cba251b81620898adc274761e411262ca4742341d3`); no install or environment mutation was requested.

- Current-main `golden_desktop_demo_v3.py doctor`: **12/15**, exit 1. Linux/WSLg, X11 connection, WSL Python imports, Windows Python and Node passed. `windows_cli` and `chromium` were unconfigured; dependent `codex_cli` therefore also failed. This is a prerequisite HOLD, not an acceptance pass.
- Current-main `golden_desktop_demo_v3.py audit-retained`: **FAIL**, exit 1, while the frozen report still says `RETAIN`; all three arms retain six tasks, with input tokens plain 63,128 / ephemeral 63,779 / persistent 26,563 and observed break-even task 2. Seven current-source hashes differ: `run_integrated_efficiency_live_v1.py`, `integrated_efficiency_protocol_v1.py`, `integrated_efficiency_client_v1.py`, `integrated_efficiency_model_v1.py`, `adaptive_acquisition_caller_v2.py`, `schema_preflight_v1.py`, and `coordinate_frame_transform_v1.py`.

The direct checks are supplemental evidence only. They do not change the official R02 classification, demonstrate runtime acceptance, or authorize changing the retained audit predicate. Preserve the mismatch as a separate source-custody blocker to investigate against the frozen preregistration and exact source archive. No live mode, allocation, GUI action, model call, installation, or task action occurred. Exact commands, conditions, stdout/stderr and exit codes are covered by this packet's regenerated `SHA256SUMS.txt`.
