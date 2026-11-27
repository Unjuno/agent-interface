# Research Preview supported-host doctor R07

The current WSL/WSLg host passed 13/15 doctor checks. Linux/WSLg, X11 connectivity, Python imports, Windows Python/Node discovery, and the configured Windows Chrome path passed. `windows_cli` failed because the expected Codex CLI JavaScript entrypoint is absent; dependent `codex_cli` also failed. The process exited 1. The raw JSON and exact process exit code are retained under `raw/`.

This rerun confirms the prior R06 blocker on the current host; it does not pass supported-host setup. The runtime/RC code relevant to the doctor is unchanged between the R06 evidence base and current main. No Chrome process, GUI, model, provider, or live task was started. The fresh no-retry Golden run and final `audit-live` remain gated. Do not install or substitute the desktop executable for the missing CLI JS as part of this result.

See [conditions](CONDITIONS.md) and the prior [R06 reused-venv doctor](../research_preview_reused_pinned_venv_doctor_r06_20261123/RESULT.md).
