# V39 Windows App Server launcher portability A02 — 2026-10-12

## H / T / D / C / U

- **H:** At main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`, V39's `app_server_command()` always selected a WSL Node/npm CLI. An opt-in direct Windows Codex executable should allow the controller to use the host's App Server while preserving the legacy path and disabled feature flags.
- **T:** A focused test against the frozen source first failed for direct executable selection and passed for the legacy default. After patching the launcher, the actual controller-import tests passed. The current installed Codex executable is `codex-cli 0.160.0`, SHA256 `37762753b554982eef1c109303d1be652b6397f1479e844794353a85650199c6`; it matches the executable in the retained A01 App Server preflight.
- **D:** Added the opt-in environment variable `AGENT_INTERFACE_CODEX_APP_SERVER_EXE`. Command construction retains the legacy Node/npm default and disabled feature flags, reads only MCP section names from the selected config, and emits an `enabled=false` override for each declared server. It emits no MCP overrides when no config exists; Codex 0.160.0 rejects overrides for undeclared names as `invalid transport`. Fixed the V39 app-server client's Windows close path to close stdio wrappers after process termination and reader shutdown.
- **C:** A corrected three-arm probe with an explicitly enabled local fake MCP confirmed baseline starts it, an empty-table override also starts it, and `mcp_servers.probe.enabled=false` suppresses its sentinel. The actual Windows command initialized against an isolated config containing an explicitly enabled fake MCP; it returned the isolated `codexHome`. A credential-free copy of the user's config also initialized with only its declared `openaiDeveloperDocs` and `node_repl` entries disabled. No model turn, game process, GUI session, or Doom input was started. Probe outputs are retained outside the repository at `D:\codex-research\win-appserver-launch-a05\mcp-config-probe`.
- **U:** V39 client-managed protocol lifecycle beyond initialize/initialized, live health/ammo observations, interruption timing, physical key release, useful feedback, recovery, ammunition/progress, terminal result, and Issue #59 successor acceptance remain unverified. This portability change does not satisfy the live-control acceptance gate.

## Result

The initial baseline test reproduced the defect: the direct-executable case returned the WSL Node/npm command. The change and two focused regression tests pass alongside the existing V39 controller tests:

- With `AGENT_INTERFACE_CODEX_APP_SERVER_EXE` set to the installed Codex 0.160.0 executable, `py -m unittest discover -s research/doom -p 'test_map01_overlap_controller_v39*.py' -v`: **20 passed**, including an actual Windows App Server initialize handshake against an isolated config.
- The same command under `py -O`: **20 passed**.
- `py -m py_compile map01_overlap_controller_v39.py`: **passed**.
- `git diff --check`: **passed**.

Tests ran on Windows with Python 3.13. The added tests validate direct executable selection, configured-only MCP disable overrides, actual Windows initialization through the production client against an isolated config, closed stdio wrappers after shutdown, and unchanged legacy fallback. PR/local test success is not a live-control result.

The isolated runtime probe directly confirmed the config behavior that the older startup study recorded: an empty-table `-c` override leaves the explicitly enabled fake MCP active, while its individual `enabled=false` override prevents startup. Earlier probe artifacts are retained alongside the corrected condition-specific rerun and its raw output. A real-profile attempt without a copied config failed before initialization because Codex fell back to the real Windows profile and rejected nonexistent override names; no real MCP was started. The current regression writes a minimal MCP config only into an isolated `CODEX_HOME`, uses no auth file, and verifies `initialize` reports that isolated home. A separate runtime probe exercised thread startup with the fake MCP, then confirmed its sentinel stayed absent under the disable override.

## Review correction

The first A02 draft proposed `-c mcp_servers={}` based on the A01 local preflight note. Review identified that this contradicted the repository's retained startup study, which explicitly tested the override and found it did not clear configured servers. The first draft's direct-mode unit test only checked argument presence and could not establish clearing behavior. The follow-up also found that emitting overrides for names absent from a Codex config causes `invalid transport`. The launcher now derives only configured server names, and the actual fake-server and isolated-profile probes verify the runtime effect. This remains launcher validation, not live control.

## Provenance

- Source: `research/doom/map01_overlap_controller_v39.py` at main blob `000d206310afe054fcddf66d9c417da46e0b3b2d`; the follow-up also edits `research/live_control/codex_app_server_client_v2.py` to close Windows-owned process streams.
- Added regression: `research/doom/test_map01_overlap_controller_v39_appserver_command.py`.
- Branch base: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- A01 preflight record: `research/doom/v39_windows_appserver_portability_a01_20261008.md` in the retained local worktree; A02 reran the App Server handshake directly and through the production V39 client against credential-free isolated config homes.
- Issue #59 was OPEN and unassigned at the time of the current-state check. PR #8837 is the review candidate for this launcher change; the existing PR #8835 is a separate release-receipt change.
- Local raw stdout/stderr and source hashes are retained at `D:\codex-research\win-appserver-launch-a05`.
