# V39 Windows App Server launcher portability A02 — 2026-10-12

## H / T / D / C / U

- **H:** At main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`, V39's `app_server_command()` always selected a WSL Node/npm CLI. An opt-in direct Windows Codex executable should allow the controller to use the host's App Server while preserving the legacy path and disabled feature flags.
- **T:** A focused test against the frozen source first failed for direct executable selection and passed for the legacy default. After patching the launcher, the actual controller-import tests passed. The current installed Codex executable is `codex-cli 0.160.0`, SHA256 `37762753b554982eef1c109303d1be652b6397f1479e844794353a85650199c6`; it matches the executable in the retained A01 App Server preflight.
- **D:** Added the opt-in environment variable `AGENT_INTERFACE_CODEX_APP_SERVER_EXE`. When set, command construction uses `[executable, "app-server", "--stdio"]`, retains every disabled feature flag, and individually disables each configured MCP using the repository's measured `mcp_servers.<name>.enabled=false` overrides. When unset, Node/npm remains the default. The empty-table override was removed after review because the existing startup study found that it does not clear configured servers.
- **C:** An isolated three-arm probe on the same Codex 0.160.0 binary used separate `CODEX_HOME` configs and a local fake MCP that only writes a sentinel and serves initialize/list. Baseline and `mcp_servers={}` both started it; `mcp_servers.probe.enabled=false` did not. The probe started an ephemeral thread but no model turn, game process, GUI session, or Doom input. The client logged a background Responses websocket 401; it produced no model result or usage. Full stdout/stderr are retained in the local probe directory.
- **U:** Integrated V39 startup against the current Windows host configuration, protocol lifecycle through the V39 client, live health/ammo observations, interruption timing, physical key release, useful feedback, recovery, ammunition/progress, terminal result, and Issue #59 successor acceptance remain unverified. This portability change does not satisfy the live-control acceptance gate.

## Result

The initial baseline test reproduced the defect: the direct-executable case returned the WSL Node/npm command. The change and two focused regression tests pass alongside the existing V39 controller tests:

- `py -m unittest discover -s . -p 'test_map01_overlap_controller_v39*.py' -v`: **18 passed**.
- `py -O -m unittest discover -s . -p 'test_map01_overlap_controller_v39*.py' -v`: **18 passed**.
- `py -m py_compile map01_overlap_controller_v39.py`: **passed**.
- `git diff --check`: **passed**.

Tests ran on Windows with Python 3.13. The added tests validate direct executable selection, individual MCP disable overrides, and unchanged legacy fallback. PR/local test success is not a live-control result.

The isolated runtime probe directly confirmed the config behavior that the older startup study recorded: an empty-table `-c` override leaves the configured fake MCP active, while its individual `enabled=false` override prevents startup. The first probe script had a shared-sentinel path bug; its original files are retained. The condition-specific sentinel rerun is `mcp-config-probe/RESULT-v2.json` and its per-arm stdout/stderr files.

## Review correction

The first A02 draft proposed `-c mcp_servers={}` based on the A01 local preflight note. Review identified that this contradicted the repository's retained startup study, which explicitly tested the override and found it did not clear configured servers. The first draft's direct-mode unit test only checked argument presence and could not establish clearing behavior. This correction adopts the previously measured per-server overrides and strengthens the command-construction test. No claim is made that the isolated fake-server probe settled runtime behavior.

## Provenance

- Source: `research/doom/map01_overlap_controller_v39.py` at main blob `000d206310afe054fcddf66d9c417da46e0b3b2d`.
- Added regression: `research/doom/test_map01_overlap_controller_v39_appserver_command.py`.
- Branch base: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- A01 preflight record: `research/doom/v39_windows_appserver_portability_a01_20261008.md` in the retained local worktree; A02 did not rerun the App Server handshake.
- Issue #59 was OPEN and unassigned at the time of the current-state check. PR #8837 is the review candidate for this launcher change; the existing PR #8835 is a separate release-receipt change.
- Local raw stdout/stderr and source hashes are retained at `D:\codex-research\win-appserver-launch-a05`.
