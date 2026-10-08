# Native integration checks: one local/CI entry point

The default local route is Linux or Ubuntu on WSL, with one reused Python
environment. Docker Desktop is not required. See [WSL-native development](../WSL_NATIVE.md)
for the Windows migration and optional WSLc isolation route. GitHub availability and model-host tool discovery are not prerequisites.
This entry point exercises the existing protocol and inert harness contracts;
it does not start a GUI, call a model or certify application performance.

With one Python environment containing the dependencies:

```sh
python3 -m venv .venv-native-checks
.venv-native-checks/bin/python -m pip install -r research/live_control/requirements-native-mcp.txt Pillow==10.2.0 numpy==1.26.4 python-xlib==0.33
.venv-native-checks/bin/python runtime/integration_checks/native.py --output results-local/native-check-01
```

For the existing split WSL environments, no reinstallation is required:

```sh
python3 runtime/integration_checks/native.py \
  --protocol-python /tmp/agent-interface-mcp-venv/bin/python \
  --harness-python /usr/bin/python3 \
  --output results-local/native-check-01
```

From Windows, the [WSL launcher](wsl-native.ps1) calls this same runner without
Docker or dependency installation; see [the direct invocation](../WSL_NATIVE.md#repeat-checks-from-windows-without-reinstalling-dependencies).

Use a fresh output path each time. The runner sets its own repository import
paths, runs both fixed suites, retains full stdout/stderr with hashes, and writes
result.json. It exits nonzero if either suite fails or its interpreter cannot
start. Existing output directories are never overwritten. A local PASS describes
only these tests; GUI use, effect scoring and performance evidence are separate.

The Native MCP GitHub workflow calls this same script and uploads the result and
logs even on a failed test run. Suite membership has one source of truth here,
including public read-only observation (initialization/capture/close failures and
no input dispatch), explicit-display backend selection without environment
mutation, key-repeat expansion/capacity checks and lossless receipt-reference
round trips. Reference-shaped literal data, unknown fields, booleans versus
numbers, and malformed reference chains remain covered. Two interpreters are optional;
CI uses a single installed environment. No sensor development is included.

## Optional legacy Docker environment matching the native CI checks

Build once from the repository root (dependency installation requires network):

```sh
docker build -f runtime/integration_checks/Dockerfile -t agent-interface-native-checks:local .
```

Then run offline with source read-only and a dedicated writable result directory.
For PowerShell, from the repository root:

```powershell
$nativeSource = (Get-Location).Path
$nativeOutput = (New-Item -ItemType Directory -Path results-local/native-docker-01).FullName
docker run --name ai-native-check-01 --network none --read-only --memory 512m `
  --tmpfs /tmp:rw,size=128m `
  --mount "type=bind,source=$nativeSource,target=/src,readonly" `
  --mount "type=bind,source=$nativeOutput,target=/out" `
  agent-interface-native-checks:local --output /out/checks
```

Use new output/container names for each run and keep the checkout unchanged
while checks run. The `/out/checks` directory must not already exist. Inspect
`checks/result.json` and the retained logs; a container start alone is not a
test result. Record `git rev-parse HEAD`, local changes and `docker image inspect
agent-interface-native-checks:local --format '{{.Id}}'` with the evidence.

The base image and direct dependency versions are pinned; transitive Python
dependencies are resolved during build, so rebuilds are not claimed byte-identical.
Record the built image ID or reuse the same image for a comparison. This image
is for the fixed native contract suites, not broad test discovery, distribution
building, a display server, GUI input or model inference. It needs no host display
socket, Docker socket, credentials or network access during the checks.

## Inspect a retained host timeline

`python3 -m runtime.integration_checks.host_timing /absolute/transport` emits a
read-only JSON summary of one instrumented relay lifetime. It binds replies and
review declarations to their recorded hashes, distinguishes incomplete operations,
and reports host send/reply/presentation/review boundaries separately. This needs
only Python's standard library. See [the timing contract](../../research/live_control/RELAY_HOST_TIMELINE.md#read-only-timing-summary)
and [retrospective primary-use evidence](../results/host-timing-summary-01/README.md).
It cannot measure model ingestion, independent semantic completion or model tokens.

## Count reported work separately from transport replies

Run `python3 -m runtime.integration_checks.workload /absolute/host-directory` after a retained host lifetime. It validates the host timeline, hashes the same replies, and counts explicit public dispatch completion/refusal/failure separately from relay refusal and unknown results. Other tool calls remain counted by name. Unsupported receipt forms stay unclassified. No input is dispatched.

This is receipt accounting, not task scoring: a completed input can have the wrong visible effect, a refused action does not prove all earlier input had no effect, and a repair requires independent attribution. Per-call release verification, inspection results and presentation/review counts remain visible. Partial timelines are not repaired or silently excluded. See [four retained inventories](../results/retained-workload-01/README.md).

## Native MCP CI source checkout

The Native MCP workflow uses non-cone sparse patterns for the runtime packages
and files directly under `research/live_control`. The same47 Node host checks and
fixed Python protocol/harness suites run; top-level research modules, requirements
and source-gate inputs remain available. Nested historical research bundles are
not materialized in this contract-test job. The bundles remain committed in Git.

The [matched source-scope record](../results/native-ci-source-scope-01/README.md)
checks the exact same commit with the old and candidate selections:35,718 files /
2,864,509,379 bytes versus2,089 files /10,115,800 bytes, all candidate bytes matching
the baseline. Both selections passed47 Node,324 protocol and141 harness tests.
This local worktree pair shares Git objects and excludes network transfer; its
size comparison is not a remote checkout-speed or GUI-performance claim. Local
Node24 differs from CI's Node22, so remote tests are still required.

A future test needing a nested source or fixture directory must include that
specific dependency in the workflow patterns. Missing dependencies must fail the
existing tests; reducing the checked-out source scope does not authorize skipping
tests or changing frozen study inputs. The5-minute job timeout and suite commands
are unchanged. Non-cone patterns are supported by
[actions/checkout v4](https://github.com/actions/checkout/blob/v4/README.md#fetch-only-a-single-file).