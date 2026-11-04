#!/usr/bin/env bash
set -u

packet_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$packet_dir/../../.." && pwd)"
raw_dir="$packet_dir/raw"
python_bin="${AGENT_INTERFACE_TEST_PYTHON:-/home/user/.cache/agent-interface-xvfb-pr10226-20261105/venv/bin/python}"
mkdir -p "$raw_dir"

if [[ ! -x "$python_bin" ]]; then
  echo "pinned test interpreter is missing: $python_bin" >&2
  exit 2
fi
"$python_bin" -c 'import mcp, numpy, PIL, Xlib; from importlib.metadata import version; assert version("python-xlib") == "0.33"; assert version("Pillow") == "10.2.0"; assert version("numpy") == "1.26.4"; assert version("mcp") == "1.30.0"' \
  >"$raw_dir/dependency-check.stdout.log" 2>"$raw_dir/dependency-check.stderr.log"
dependency_status=$?
echo "$dependency_status" >"$raw_dir/dependency-check.exitcode.txt"
if [[ "$dependency_status" -ne 0 ]]; then
  echo "pinned dependency check failed; no trial was started" >&2
  exit "$dependency_status"
fi

{
  date -u +'%Y-%m-%dT%H:%M:%SZ'
  uname -a
  dpkg-query -W -f='xvfb=${Version}\n' xvfb 2>&1 || true
  "$python_bin" --version
  "$python_bin" -m pip freeze
  echo 'source_sha=57573394c4d88988a40b0e57c270c945a3a621cd'
} >"$raw_dir/run-metadata.txt"

for trial in A1:0 B1:1 B2:1 A2:0; do
  name="${trial%%:*}"
  prestarted="${trial##*:}"
  case "$name" in A1|B1|B2|A2) display_number=88 ;; *) echo "unexpected preregistered trial: $name" >&2; exit 2 ;; esac
  display=":$display_number"
  socket="/tmp/.X11-unix/X$display_number"
  if [[ -e "$socket" ]]; then
    echo "display socket already exists: $socket; stopping before trial $name" \
      | tee "$raw_dir/$name.setup-failure.txt"
    exit 3
  fi

  auth_file="$raw_dir/$name.auth"
  xvfb_log="$raw_dir/$name.xvfb.log"
  : >"$auth_file"
  Xvfb "$display" -screen 0 1024x768x24 -ac >"$xvfb_log" 2>&1 &
  xvfb_pid=$!
  sleep 0.5
  if ! kill -0 "$xvfb_pid" 2>/dev/null; then
    echo "private Xvfb failed to start on $display" \
      | tee "$raw_dir/$name.setup-failure.txt"
    wait "$xvfb_pid" 2>/dev/null || true
    exit 4
  fi

  set +e
  (
    cd "$repo_root" || exit 10
    export DISPLAY="$display"
    export XAUTHORITY="$auth_file"
    export AGENT_INTERFACE_XVFB_PID="$xvfb_pid"
    export AGENT_INTERFACE_MCP_XVFB_TEST=1
    export AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=1.0
    export AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1
    export AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR="$prestarted"
    export AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT="$raw_dir/$name.json"
    timeout --signal=TERM --kill-after=10s 210s \
      "$python_bin" -m unittest -v \
      runtime.cli_v1.test_mcp_xvfb_blocked_release_integration
  ) >"$raw_dir/$name.stdout.log" 2>"$raw_dir/$name.stderr.log"
  trial_status=$?
  set -e
  echo "$trial_status" >"$raw_dir/$name.exitcode.txt"

  kill "$xvfb_pid" 2>/dev/null || true
  wait "$xvfb_pid" 2>/dev/null || true
  if kill -0 "$xvfb_pid" 2>/dev/null; then
    echo "owned Xvfb did not exit after trial $name; stopping sequence" \
      | tee "$raw_dir/$name.cleanup-failure.txt"
    exit 5
  fi
  if [[ ! -s "$raw_dir/$name.json" ]]; then
    echo "trial $name did not retain its JSON report; preserving attempt and stopping" \
      | tee "$raw_dir/$name.report-missing.txt"
    exit 6
  fi

  if grep -q '"status": "FAIL_CLEANUP"' "$raw_dir/$name.json"; then
    echo "trial $name reports failed cleanup; preserving attempt and stopping" \
      | tee "$raw_dir/$name.cleanup-failure.txt"
    exit 7
  fi
done

echo "All four preregistered attempts executed once; inspect raw reports before scoring."
