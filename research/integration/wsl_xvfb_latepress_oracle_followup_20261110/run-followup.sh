#!/usr/bin/env bash
set -u

packet_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$packet_dir/../../.." && pwd)"
raw_dir="${AGENT_INTERFACE_FOLLOWUP_OUTPUT:-}"
python_bin=/usr/bin/python3

if [[ -z "$raw_dir" ]]; then
  echo 'AGENT_INTERFACE_FOLLOWUP_OUTPUT must name a fresh writable output directory' >&2
  exit 2
fi
mkdir -p "$raw_dir"
if [[ -n "$(find "$raw_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  echo "output directory is not empty: $raw_dir" >&2
  exit 2
fi
if [[ ! -x "$python_bin" ]]; then
  echo "pinned interpreter is missing: $python_bin" >&2
  exit 2
fi

"$python_bin" -c 'import mcp, numpy, PIL, Xlib; from importlib.metadata import version; assert version("python-xlib") == "0.33"; assert version("Pillow") == "10.2.0"; assert version("numpy") == "1.26.4"; assert version("mcp") == "1.30.0"' \
  >"$raw_dir/dependency-check.stdout.log" 2>"$raw_dir/dependency-check.stderr.log"
dependency_status=$?
echo "$dependency_status" >"$raw_dir/dependency-check.exitcode.txt"
if [[ "$dependency_status" -ne 0 ]]; then
  echo 'dependency preflight failed; no input trial started' >&2
  exit "$dependency_status"
fi

{
  date -u +'%Y-%m-%dT%H:%M:%SZ'
  uname -a
  dpkg-query -W -f='xvfb=${Version}\n' xvfb 2>&1 || true
  "$python_bin" --version
  "$python_bin" -m pip freeze
  git -C "$repo_root" rev-parse HEAD 2>&1 || true
} >"$raw_dir/run-metadata.txt"

for spec in A100:0:100 B100:1:100 B250:1:250 A250:0:250 A250r:0:250 B250r:1:250 B100r:1:100 A100r:0:100; do
  name="${spec%%:*}"
  rest="${spec#*:}"
  prestarted="${rest%%:*}"
  delay_ms="${rest##*:}"
  display=':88'
  socket=/tmp/.X11-unix/X88
  if [[ -e "$socket" ]]; then
    echo "private display socket already exists before $name: $socket" \
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
    export AGENT_INTERFACE_MCP_XVFB_DELAY_MS="$delay_ms"
    export AGENT_INTERFACE_MCP_XVFB_CONTINUE_AFTER_NONNEUTRAL_RELEASE=1
    export AGENT_INTERFACE_MCP_XVFB_OBLIGATION_PUBLISHER_TRACE="$raw_dir/$name-obligations.jsonl"
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
    echo "owned Xvfb did not exit after $name; stopping sequence" \
      | tee "$raw_dir/$name.cleanup-failure.txt"
    exit 5
  fi
  if [[ ! -s "$raw_dir/$name.json" ]]; then
    echo "trial $name has no retained JSON; preserving attempt and stopping" \
      | tee "$raw_dir/$name.report-missing.txt"
    exit 6
  fi
  if grep -q '"status": "FAIL_CLEANUP"' "$raw_dir/$name.json"; then
    echo "trial $name reports failed cleanup; preserving attempt and stopping" \
      | tee "$raw_dir/$name.cleanup-failure.txt"
    exit 7
  fi
done

echo 'All eight preregistered follow-up attempts executed once; audit reports and traces.'
