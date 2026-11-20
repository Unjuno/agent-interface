# Research preview RC1 setup and doctor R05

- Attempt: `RP-RC1-SETUP-DOCTOR-20261121-05`
- Frozen source: `8e5052e04f8720fe89052ad01127114dd6852d88` (canonical RC1)
- Environment: Ubuntu WSL2/WSLg on ext4, Python 3.12.3, Git 2.43.0
- Decision: **HOLD / doctor failed**. Preserve this attempt; do not treat dependency setup success as preview acceptance.

## Frozen scope

The condition file was frozen before execution. One explicit `--install-dependencies` run could install only the nine exact distributions pinned by RC1 `runtime/requirements-golden.txt` into that clone's `runtime/.venv`. No runtime package, Java, browser, or model/provider was acquired. No GUI demo, input, golden task, Docker, or Issue #57 allocation was used. The doctor may invoke the configured Windows Codex CLI only with `--version`.

## Observed result

The setup command installed all nine pinned distributions successfully in the isolated venv: Pillow 10.2.0, NumPy 1.26.4, python-xlib 0.33, jsonschema 4.10.3, openpyxl 3.1.2, et-xmlfile 1.1.0, attrs 26.1.0, pyrsistent 0.20.0, and six 1.17.0. The venv was confirmed present from Ubuntu WSL after the run.

The doctor exited 1 with `passed: false` (12/15 checks true). The three false checks are `windows_cli`, `chromium`, and `codex_cli`. Windows Python, Windows Node, WSLg display, X11 connection, and required Python imports passed. `codex_cli` is downstream of the absent CLI JS path. Read-only host probing found Windows Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`, but RC1 defaults to a WSL `google-chrome` command; no configured WSL Chromium was present. The Codex desktop app exposes a native `codex.exe`; the expected npm `@openai/codex/bin/codex.js` was not found in the probed locations. Neither was substituted for the RC1 CLI contract.

## Interpretation and next step

This is a reproducible environment-setup boundary, not an application/runtime failure and not a product preview pass. The packages and WSL display are ready; the host lacks the exact configured CLI and Linux Chromium executables. No further doctor retry is informative until those already-approved exact executables are present or the RC1 setup contract is deliberately revised. Do not download/install either dependency as part of model/runtime preparation. Keep Issue #58 open and retain RC1's frozen source semantics.

## Custody

- `conditions.json`: frozen preregistration.
- `raw/stdout.txt`, `raw/stderr.txt`, `raw/exit-code.txt`: captured setup/doctor output and process result.
- `SHA256SUMS`: content hashes for the frozen conditions and raw files.
- The source checkout remains at `/home/user/agent-interface-rp-rc1-doctor-r05-20261121` with its isolated venv; it was not removed.
