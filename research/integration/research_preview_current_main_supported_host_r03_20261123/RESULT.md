# Current-main WSL supported-host diagnostic R03

**Disposition: acceptance HOLD; package construction remains passed.** This is a read-only system-Python doctor diagnostic against the frozen R02 source. It does not retry the Golden task, install dependencies, launch a browser, or send input.

## Frozen target and conditions

- Source revision: `c5fc0ee00b5fa5208088ee69004a336770336ac4` (same immutable current-main tree used by package R02; package R02 was recorded before its evidence-only PR merged).
- Host: Ubuntu WSL2, kernel `6.18.58.1-microsoft-standard-WSL2`, glibc 2.39, Python 3.12.3.
- R02 acceptance runner was executed once with `--live` and `--install-dependencies` omitted. Preflight passed; setup stopped with exit 2 at the explicit dependency-install opt-in. `runtime/.venv` remained absent.
- The same frozen checkout's documented `runtime/golden-demo-v3.sh doctor` command was then run separately with system Python. Exit code 1; doctor reports 8/15 checks passed.
- No Python dependencies, runtime source, model weights, browser, CLI, container image, or other runtime were installed/downloaded. No GUI/model/live input action occurred.

## Doctor result

Passed: Linux/WSL identity, `wslpath`, `DISPLAY`, Xlib, jsonschema, Windows Python, Windows Node, and X11 connection (8/15).

Failed: Python `PIL`, `numpy`, `openpyxl`, `et_xmlfile`; Windows CLI, Chromium, and Codex CLI (7/15). The doctor reports the Windows Python and Node paths but cannot find the configured CLI or Chromium executables.

This narrows the present acceptance blockers. Installing pinned Python requirements could address four missing Python imports but would not resolve the three missing executable/configuration checks. The actual Windows-to-WSL bridge, supported-host setup, fresh no-retry Golden run and `audit-live` remain unverified. Issue #58 remains open; no release-readiness claim is made.

## Preserved evidence

- `raw/acceptance-r02/acceptance.json` and per-step stdout/stderr: exact first acceptance-run output.
- `raw/doctor.stdout.json`, `raw/doctor.stderr.txt`, `raw/doctor.exit_code.txt`: exact separate doctor output and exit status.
- `raw/SHA256SUMS`: SHA-256 for every raw file.
- Package-build evidence and bundle hash remain in [R02](../research_preview_current_main_wsl_build_r02_20261123/RESULT.md).
