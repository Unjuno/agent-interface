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
including key-repeat expansion/capacity checks and lossless receipt-reference
round trips. Reference-shaped literal data, unknown fields, booleans versus
numbers, and malformed reference chains remain covered. Two interpreters are optional;
CI uses a single installed environment. No sensor development is included.
