# V39 Windows App Server launcher portability A02 — 2026-10-12

## H / T / D / C / U

- **H:** At main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`, V39's `app_server_command()` always selected a WSL Node/npm CLI. An opt-in direct Windows Codex executable should allow the controller to use the host's App Server while preserving the legacy path and disabled feature flags.
- **T:** A focused test against the frozen source first failed for direct executable selection and passed for the legacy default. After patching the launcher, the actual controller-import tests passed. The current installed Codex executable is `codex-cli 0.160.0`, SHA256 `37762753b554982eef1c109303d1be652b6397f1479e844794353a85650199c6`; it matches the executable in the retained A01 App Server preflight.
- **D:** Added the opt-in environment variable `AGENT_INTERFACE_CODEX_APP_SERVER_EXE`. When set, command construction uses `[executable, "app-server", "--stdio"]`, retains every disabled feature flag, and applies `-c mcp_servers={}` to avoid parsing configured host MCP transports. When unset, Node/npm and the existing per-MCP disable overrides remain unchanged.
- **C:** This run covers command construction and existing V39 unit regressions only. No App Server handshake was repeated because A01 already retained a successful initialize/initialized/exit preflight on the same binary SHA. No model turn, game process, GUI session, Doom input, or task-effect claim was made.
- **U:** Integrated V39 startup against the current Windows host configuration, protocol lifecycle through the V39 client, live health/ammo observations, interruption timing, physical key release, useful feedback, recovery, ammunition/progress, terminal result, and Issue #59 successor acceptance remain unverified. This portability change does not satisfy the live-control acceptance gate.

## Result

The initial baseline test reproduced the defect: the direct-executable case returned the WSL Node/npm command. The change and two focused regression tests pass alongside the existing V39 controller tests:

- `py -m unittest discover -s . -p 'test_map01_overlap_controller_v39*.py' -v`: **18 passed**.
- `py -O -m unittest discover -s . -p 'test_map01_overlap_controller_v39*.py' -v`: **18 passed**.
- `py -m py_compile map01_overlap_controller_v39.py`: **passed**.
- `git diff --check`: **passed**.

Tests ran on Windows with Python 3.13. The added tests validate both direct executable selection and unchanged legacy fallback. PR/local test success is not a live-control result.

## Provenance

- Source: `research/doom/map01_overlap_controller_v39.py` at main blob `000d206310afe054fcddf66d9c417da46e0b3b2d`.
- Added regression: `research/doom/test_map01_overlap_controller_v39_appserver_command.py`.
- Branch base: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- A01 preflight record: `research/doom/v39_windows_appserver_portability_a01_20261008.md` in the retained local worktree; A02 did not rerun the App Server handshake.
- Issue #59 was OPEN and unassigned at the time of the current-state check. An exact-match open PR for this environment variable was not found. Existing PR #8835 is a separate release-receipt change.
- Local raw stdout/stderr and source hashes are retained at `D:\codex-research\win-appserver-launch-a05`.
