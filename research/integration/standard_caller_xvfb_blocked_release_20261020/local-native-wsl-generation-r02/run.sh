#!/usr/bin/env bash
set -euo pipefail
repo=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/agent-interface-repository-consolidation-plan
out="$repo/research/integration/standard_caller_xvfb_blocked_release_20261020/local-native-wsl-generation-r02"
python=/tmp/agent-interface-xvfb-blocked-release-r01/bin/python
{
  cat /etc/os-release
  uname -a
  "$python" --version
  "$python" -m pip freeze
  dpkg-query -W -f='${binary:Package}=${Version}\n' xvfb || true
} > "$out/environment.txt" 2>&1
Xvfb :89 -screen 0 1024x768x24 -ac -nolisten tcp > "$out/xvfb.log" 2>&1 &
xvfb_pid=$!
cleanup() {
  kill -TERM "$xvfb_pid" 2>/dev/null || true
  wait "$xvfb_pid" 2>/dev/null || true
  if [ -e "/proc/$xvfb_pid" ]; then
    printf 'private_xvfb_pid=%s state=present\n' "$xvfb_pid" > "$out/xvfb-after-run.txt"
  else
    printf 'private_xvfb_pid=%s state=absent\n' "$xvfb_pid" > "$out/xvfb-after-run.txt"
  fi
}
trap cleanup EXIT
export DISPLAY=:89
export PYTHONPATH="$repo"
export AGENT_INTERFACE_XVFB_PID="$xvfb_pid"
export AGENT_INTERFACE_MCP_XVFB_TEST=1
export AGENT_INTERFACE_MCP_XVFB_RESULT="$out/result.json"
export AGENT_INTERFACE_MCP_XVFB_IMAGE_RESULT="$out/result.observation.png"
for n in 1 2 3 4 5 6 7 8 9 10; do
  if "$python" -c 'from Xlib import display; d=display.Display(); d.close()' >/dev/null 2>&1; then break; fi
  sleep 0.2
done
set +e
"$python" -m unittest -v runtime.cli_v1.test_mcp_xvfb_generation_integration > "$out/stdout.txt" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$out/exit-code.txt"
exit "$status"
