# Runtime

This directory is reserved for the user-facing Agent Interface runtime.

The project is still research-first, so experimental benchmark code remains under `research/`. Code moves here only when it represents the current promoted semantics rather than a one-off experiment.
## Directory map

| Path | Role |
|---|---|
| [`core_v1/`](core_v1/) | Promoted platform-neutral runtime contract and admission semantics. |
| [`kernel/`](kernel/) | Platform-neutral mechanical lifecycle seam. |
| [`interface_v1/`](interface_v1/) | Side-effect-free native discovery/doctor facade. |
| [`selector_v1/`](selector_v1/) | Runtime backend selection layer. |
| [`cli_v1/`](cli_v1/) | Model/vendor-neutral local CLI/API entry point. |
| [`backends/`](backends/) | Native X11, Win32, and Quartz backend candidates; see each backend's README for its evidence boundary. |
| [`distribution_v1/`](distribution_v1/) | Standalone doctor/bootstrap distribution work. |
| [`distribution_v2/`](distribution_v2/) | Portable unified runtime zipapp work. |
| [`integration_checks/`](integration_checks/) | Shared local/CI checks for native integration; runs in WSL without Docker or model-host tool discovery. |
| [`results/`](results/) | Retained runtime-result artifacts where applicable. |
| `golden_desktop_*`, `golden-demo-*`, `setup-golden-demo*` | Current golden desktop demonstration runners, audits, preregistration, and reports. |

Directory presence does not by itself establish platform support. Support claims remain bounded by each component's retained evidence and the user-facing release contract.


## Target properties

A runtime preview should be:

- quick to install or unpack;
- agent- and model-agnostic;
- usable on unknown applications through universal control;
- responsive enough that the agent is not blocked waiting for avoidable interface latency;
- local-first for deterministic control, feedback, verification, and recovery;
- explicit about uncertainty and able to fall back safely.

See `../docs/principles.md` for the design constraints.

## Planned surface

The eventual runtime is expected to expose a small local library/protocol surface plus a thin CLI for setup, inspection, and demos. High-frequency control should not require spawning a new process or crossing a remote boundary for each action.

## Golden desktop demo

The first promoted entry point packages the retained six-task Chromium workflow.
It runs under Linux/X11 (the current tested host is WSLg), uses the same checked
input runtime and independent exact-token scorer, and keeps the frozen comparison
sources unchanged.

```bash
./runtime/setup-golden-demo-v3.sh
./runtime/golden-demo-v3.sh doctor
./runtime/golden-demo-v3.sh audit-retained
./runtime/golden-demo-v3.sh run
./runtime/golden-demo-v3.sh audit-live artifacts-local/golden-desktop-YYYYMMDD-HHMMSS
```

The setup script creates `runtime/.venv`, installs the nine pinned distributions in
`requirements-golden.txt`, and runs the fifteen-check v3 `doctor`. It does not install Chrome or
Codex; missing external executables remain explicit doctor failures.

`doctor` checks the display, every direct GUI Python dependency, Chromium and the Codex CLI bridge.
`audit-retained` verifies source hashes and the published fixed comparison without
making a model call or opening a GUI. `run` creates a new timestamped directory
under the ignored `artifacts-local/` directory, performs a fresh schema preflight, then runs only the
persistent A/A/A/B/B/B path: cold compilation, two warm reuses, stale-reference
refusal and repair, then two post-repair reuses. It never overwrites an earlier
run and performs no automatic retry.
`audit-live` recomputes call accounting, exact submissions, the stale-reference
refusal, repair, and every terminal input release from the retained raw records.

The current task-grounding bridge uses two turns on one capability-minimized
Codex app-server thread.  The schema preflight remains a separate compatibility
call.  The first frozen v3 run completes 6/6 exact tasks with zero stale pointer
admission and57/57 verified releases; its single-run evidence and limits are in
`GOLDEN_DESKTOP_DEMO_V3.md`.

The model bridge uses the Windows Codex installation from WSL. Unique
paths are discovered under `/mnt/c/Users`; set these when discovery is ambiguous:

```bash
export AGENT_INTERFACE_WINDOWS_PYTHON=/mnt/c/Users/you/AppData/Local/Programs/Python/Python312/python.exe
export AGENT_INTERFACE_WINDOWS_NODE='/mnt/c/Program Files/nodejs/node.exe'
export AGENT_INTERFACE_WINDOWS_CODEX_JS=/mnt/c/Users/you/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js
export AGENT_INTERFACE_CHROMIUM=/usr/bin/google-chrome
```

This is a Research Preview path. A fresh persistent-only run checks mechanics and
correctness; it does not reproduce the three-arm efficiency comparison or prove
human-level speed and general GUI reliability.
