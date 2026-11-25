# Win32 R02 offline package

This research packet builds from the vendored assets in `inputs`. The pin list records the SHA-256 of the selected frozen R44 assets and the R02 runner and fixture candidates. Frozen Python inputs are stored as text to keep the exact bytes available for comparison. The builder adds unconditional refusal to the packaged runner's `main` and `run_trial` entry points and retains its direct-execution refusal.

The build creates a template and prospective conditions with deterministic example IDs and zero live allocation. It keeps historical R44 conditions separately and initializes the packaged cohort ledger with zero trials. The selected R44 task server, scorer, and foreground probe occupy the exact paths expected by the runner.

The output directory must be a new packet directly under `<root>/research/integration`. The builder checks how the actual runner and task-server sources resolve their repository roots at the requested output path before publishing it. It probes the B task and B recovery paths in disposable copies. Each probe loads the pinned R44 task-server entrypoint with a fake MCP constructor and calls only initialization and tool listing. The probe records zero fixture launches, tool calls, native runtime startups, and host custody accesses. Production server registration, Win32 input, and persistent custody remain outside this verification.

Run from this directory with Python 3.11 and the MCP Python package installed.

```powershell
$checkRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("r02-" + [guid]::NewGuid())
$integration = Join-Path $checkRoot "research/integration"
New-Item -ItemType Directory -Path $integration | Out-Null
python -B build_offline_package.py --output (Join-Path $integration "r02-offline")
python -B -m unittest -v test_offline_package
python -B -O -m unittest -v test_offline_package
```
