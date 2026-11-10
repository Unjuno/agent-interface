# Runtime

This directory is reserved for the user-facing Agent Interface runtime.

The project is still research-first, so experimental benchmark code remains under `research/`. Code moves here only when it represents the current promoted semantics rather than a one-off experiment.
Start with [Using the current interface](USING_CURRENT_INTERFACE.md) for public action/image output, native continuation and local verification.

For local Linux-container research on Windows, use the scoped [WSL Containers (WSLc) migration guide](../.github/wslc-local-containers.md) before starting Docker Desktop. WSLc is the preferred pilot for eligible single-container iterations; it is not a blanket replacement for Docker/OrbStack. In particular, this host has **not** demonstrated effective memory/swap enforcement, so do not treat `--memory` as a hard safety ceiling. Keep Docker-specific, Compose/API-dependent, frozen-runtime, and hosted-CI workflows on their declared runtimes until separately validated.

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
| [`results/`](results/) | Retained runtime-result artifacts where applicable; see the [relay admission history](results/relay-admission-lineage-01a0ff58/README.md) for scoped historical UTF-8/JSON boundary evidence. |
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
./runtime/setup-golden-demo-v3.sh --install-dependencies
./runtime/golden-demo-v3.sh doctor
./runtime/golden-demo-v3.sh audit-retained
./runtime/golden-demo-v3.sh run
./runtime/golden-demo-v3.sh audit-live artifacts-local/golden-desktop-YYYYMMDD-HHMMSS
```

### Runtime acquisition, dependency preparation, and model access are separate

**Nothing is downloaded or installed merely by reading this guide or invoking a setup
script without its explicit flag.** A user who wants a runnable runtime must first
choose and explicitly perform one of these acquisition paths: check out the source,
build the portable archive locally, or retrieve a platform artifact produced by CI.
There is no supported command that silently downloads and installs a runtime package.
The setup scripts below do not perform any of those runtime-acquisition steps.

Nothing in the setup path implicitly acquires the runtime package or model weights. The setup
flag authorizes only creation of `runtime/.venv`, download and installation of the pinned Python
dependencies, and the following local `doctor` check. It does not authorize a checkout, portable
runtime artifact retrieval, model/provider setup, GUI application install, Codex install, or image
pull. Treat each as its own explicit action:

| Action | Current path | What it acquires |
|---|---|---|
| Get runtime source | Explicitly clone/checkout the repository and chosen revision. | Source files only; no model weights or provider setup. |
| Build the portable runtime | Explicitly run `python -m runtime.distribution_v2.build` with output paths. | A local `.pyz` plus manifest/checksum; this build reads committed source and performs no network acquisition. |
| Retrieve a built runtime | Explicitly retrieve the `portable-runtime-<platform>` CI artifact and place it where intended. | A `.pyz` artifact; CI artifacts are not a release, and setup does not retrieve or install them. |
| Prepare golden-demo Python dependencies | Explicitly pass `--install-dependencies` to the setup script. | Creates `runtime/.venv`, installs the nine pinned distributions from `requirements-golden.txt`, then runs the local fifteen-check v3 `doctor`. This does not get or install the runtime package. |
| Use a model/provider | Use the existing Windows Codex installation and its separately configured authorization. | The bridge invokes that provider path; it does not download model weights or install/configure the provider. |
| Install an external GUI application | Install it separately if needed. | Setup/doctor checks for Chromium and the Codex CLI bridge; it does not install them. |
| Pull a container image | Explicitly select and pull the required image in the container workflow. | Golden-demo setup does not pull images or start containers. |

There is currently no supported one-command runtime-package download/install flow or downloadable
runtime release in this research-preview path. The CI workflow only builds and uploads artifacts;
retrieving and placing one is a separate user action. The v3 setup script implements only the
dependency-install action above. Missing external executables remain explicit `doctor` failures.

This is also the boundary for any future installer: acquiring or installing the Agent Interface
runtime must be a separately named, affirmative user action. Model/provider setup and Python
dependency preparation must remain separate choices; selecting either must not implicitly download
or install the runtime package. A combined first-run flow is acceptable only when each acquisition
is independently disclosed and selected before it starts.

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


## Current public-entry integration evidence

[Primary six-task public MCP comparison](results/public-six-task-comparison-04/README.md)
records direct and guarded paths completing 6/6 exact-once submissions through the
same packaged public entry, with verified input release and explicit changed-layout
recovery. The final direct image still lacked its completion cue despite independent
success. This supports scoped correctness, not overall acceptance, causal speed/token
benefit or human-tempo operation; earlier interrupted/caller-failed trials are retained.

[Production-candidate post-release comparison](results/production-spine-main-01/README.md)
records a new primary-operated six-task pair with exact-once effects on both routes,
changed-state refusals and explicit recovery. The direct route returned all six saved
cues through optional post-release capture. Extra observations, preview failures and
the prior input-free STOP remain recorded. Provider model/settings, useful feedback,
semantic latency, tokens/cost and human-tempo benefit remain unverified.

## Runtime acquisition and consent boundaries

Agent Interface does not automatically download or install its runtime, model
weights, GUI applications, or container images. Each acquisition or execution
is a separate user action. A command that prepares one category does not grant
consent for another.

| Action | What it does | What it does not do |
|---|---|---|
| Clone/fetch this repository | Downloads source files when the user runs Git. | Does not install the runtime, Python dependencies, model weights, applications, or containers. |
| Build the portable runtime | `python -m runtime.distribution_v2.build` writes a `.pyz`, manifest, and checksum locally from committed source. | Does not download an artifact, install it, install backend dependencies, publish a release, or contact a model provider. See [`distribution_v2/README.md`](distribution_v2/README.md). |
| Install runtime Python dependencies | A user-run `pip install` or the golden-demo opt-in downloads packages from configured indexes and executes package installation code. | Does not download Agent Interface source/runtime as a separate package, model weights, Chrome/Codex, or a container image. |
| Download a runtime package | Requires a separate, explicit user action naming the package source and destination. Verify the artifact and checksum before running it. | No automatic runtime-package downloader is provided by the repository setup scripts. |
| Run a model/provider-backed demonstration | Requires its own explicit invocation and configured provider/client. It may send prompts/images to a provider and may consume account quota. | Is not authorized by source checkout, runtime build, or Python dependency installation. The runtime setup scripts do not download model weights. |
| Install a GUI application or acquire a container image | Requires a separate explicit install/pull action and target-specific review. | Is not authorized by any runtime/dependency setup option. |

The GitHub Release assets currently describe research snapshots, not the
portable runnable runtime package. Inspect a release's asset names and
checksums before treating it as an installable runtime. A source archive is
not a runtime installer.

[`setup-golden-demo.sh`](setup-golden-demo.sh) and
[`setup-golden-demo-v3.sh`](setup-golden-demo-v3.sh) require the explicit
`--install-dependencies` argument. That option creates `runtime/.venv` and
installs the pinned packages in [`requirements-golden.txt`](requirements-golden.txt),
then runs the local `doctor` command. It does not execute the demo's `run`
command or make a model/provider call. Without the exact option, each script
exits before creating the environment or contacting the package index.

There is no repository-wide `research/requirements.txt` on current main.
Research experiments may have their own dependency files and setup instructions;
review those instructions and the configured package index before a user-run
package installation. Such a command prepares only that experiment's environment.

To build the `.pyz` from a checkout, use the documented local builder:

```sh
python -m runtime.distribution_v2.build \
  --out results-local/my-runtime/agent-interface-runtime.pyz \
  --manifest results-local/my-runtime/manifest.json \
  --sums results-local/my-runtime/sha256.txt
```

This is a local build from committed source; it is not a package download or
installation. Running the archive is another explicit user action and requires
the selected Python/backend dependencies to already be available. See the
[portable runtime guide](distribution_v2/README.md) and
[CLI guide](cli_v1/README.md) for supported commands and runtime limits.

Keep setup commands narrow and fail closed when an acquisition scope is
ambiguous. Before adding an automatic package, model, application, or image
download, expose it as a separate explicit option with its source, destination,
version/checksum, and side effects. Never infer authorization for a runtime
download from model setup, or model/provider use from runtime setup.
