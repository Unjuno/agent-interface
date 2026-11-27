#!/bin/sh
set +e
X11_PROXY_TEST_EVIDENCE_DIR=/evidence python3 -B /workspace/research/integration/xvfb_tracked_runtime_request_late_input_20261110/test_x11_delivery_proxy.py > /evidence/test.log 2>&1
status=$?
cat /evidence/test.log
printf '{"exit_code":%s}\n' "$status" > /evidence/DOCKER_EXIT.json
exit "$status"
