#!/bin/sh
set +e
python3 -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb > /evidence/test.log 2>&1
status=$?
cat /evidence/test.log
printf '{"exit_code":%s,"timeout_s":45}\n' "$status" > /evidence/DOCKER_EXIT.json
exit "$status"
