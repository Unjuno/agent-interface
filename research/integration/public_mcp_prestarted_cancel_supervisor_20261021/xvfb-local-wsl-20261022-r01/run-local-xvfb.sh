#!/usr/bin/env bash
set -euo pipefail

OUT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$OUT/../../../.." && pwd)"
cd "$REPO"
VENV="$HOME/.venvs/ai-prestarted-cancel-20261022"
mkdir -p "$OUT" "$HOME/.venvs"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check --no-cache-dir \
  python-xlib==0.33 Pillow==10.2.0 numpy==1.26.4 mcp==1.30.0 \
  >"$OUT/pip-install.log" 2>&1

{
  date -u
  uname -a
  cat /etc/os-release | head -n 6
  python3 --version
  dpkg-query -W xvfb x11-xkb-utils
  "$VENV/bin/python" -m pip freeze
} > "$OUT/conditions-environment.txt"

cat > "$OUT/conditions-run.txt" <<'EOF'
source=working-tree on branch feat/prestarted-cancel-supervisor-r01
test=python -B -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration
display=:88; Xvfb 1024x768x24 -ac
cancel_ack_withhold_s=0
trace_owner_process_methods=1
prestarted_supervisor=1
injected delayed KeyPress(b)=8000ms after KeyPress(a); real Display.sync wait
no WSLc or Docker
EOF

AUTH="$OUT/prestarted-xvfb.auth"
: > "$AUTH"
Xvfb :88 -screen 0 1024x768x24 -ac >"$OUT/prestarted-xvfb.log" 2>&1 &
XVFB_PID=$!
trap 'kill "$XVFB_PID" 2>/dev/null || true; wait "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 0.5

export DISPLAY=:88 XAUTHORITY="$AUTH"
export AGENT_INTERFACE_XVFB_PID="$XVFB_PID"
export AGENT_INTERFACE_MCP_XVFB_TEST=1
export AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=0
export AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1
export AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=1
export AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT="$OUT/prestarted-cancel-xvfb.json"

set +e
timeout --signal=TERM --kill-after=10s 210s "$VENV/bin/python" -B -m unittest -v \
  runtime.cli_v1.test_mcp_xvfb_blocked_release_integration \
  >"$OUT/test.stdout.log" 2>"$OUT/test.stderr.log"
RC=$?
set -e
printf '%s\n' "$RC" > "$OUT/exit-code.txt"
exit "$RC"
