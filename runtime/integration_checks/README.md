# Native integration checks: one local/CI entry point

Run these development checks in Linux, WSL, or an already provisioned Docker
container. GitHub availability and model-host tool discovery are not prerequisites.
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

## Docker environment matching the native CI checks

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
