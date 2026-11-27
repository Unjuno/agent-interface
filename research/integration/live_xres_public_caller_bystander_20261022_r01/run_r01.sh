#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

display_name=:178
display_number=178
raw=raw/r01
mkdir -p "$raw"
if [[ -e "/tmp/.X${display_number}-lock" || -S "/tmp/.X11-unix/X${display_number}" ]]; then
  echo "HOLD: display ${display_name} is already allocated" >&2
  exit 40
fi
for existing_pid in $(pgrep -x Xvfb || true); do
  existing_cmdline=$(tr '\0' ' ' <"/proc/$existing_pid/cmdline")
  if [[ "$existing_cmdline" == *"Xvfb ${display_name} "* ]]; then
    echo "HOLD: exact Xvfb display process already exists (PID $existing_pid)" >&2
    exit 41
  fi
done
if [[ -e "$raw/result.json" ]]; then
  echo "HOLD: one-shot result already exists; refusing a rerun" >&2
  exit 42
fi

Xvfb "$display_name" -screen 0 800x600x24 -nolisten tcp -ac >"$raw/xvfb.log" 2>&1 &
xvfb_pid=$!
printf '%s\n' "$xvfb_pid" >"$raw/xvfb.pid"
cleanup() {
  if kill -0 "$xvfb_pid" 2>/dev/null; then
    kill "$xvfb_pid" 2>/dev/null || true
    wait "$xvfb_pid" 2>/dev/null || true
  fi
  if kill -0 "$xvfb_pid" 2>/dev/null; then
    echo "xvfb_alive_after_cleanup=true" >>"$raw/preflight.txt"
  else
    echo "xvfb_alive_after_cleanup=false" >>"$raw/preflight.txt"
  fi
}
trap cleanup EXIT INT TERM

export DISPLAY="$display_name"
export AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=1
export AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=0
export AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1
export AGENT_INTERFACE_XVFB_PID="$xvfb_pid"
for _ in $(seq 1 100); do
  if DISPLAY="$display_name" python3 -c 'from Xlib.display import Display; d=Display(); d.close()' >/dev/null 2>&1; then
    break
  fi
  sleep 0.05
done
DISPLAY="$display_name" python3 -c 'from Xlib.display import Display; d=Display(); d.close()'
{
  echo "xvfb_ready=true"
  echo "pid=$xvfb_pid"
  echo "exe=$(readlink -f "/proc/$xvfb_pid/exe")"
  echo "cmdline=$(tr '\0' ' ' <"/proc/$xvfb_pid/cmdline")"
  echo "package=$(dpkg-query -W -f='${binary:Package}=${Version}' xvfb)"
  python3 --version
  python3 -c 'import Xlib; print("python_xlib=" + getattr(Xlib, "__version__", "installed"))'
} >"$raw/preflight.txt"

python_bin=${AGENT_INTERFACE_WSL_PYTHON:-/home/user/.venvs/agent-interface-pipe-probe-v1/bin/python}
if [[ ! -x "$python_bin" ]]; then
  echo "HOLD: requested Python environment is not executable: $python_bin" >&2
  exit 43
fi
set +e
"$python_bin" run_live_xres_public_caller_bystander_r01.py \
  >"$raw/runner.stdout.txt" 2>"$raw/runner.stderr.txt"
runner_exit=$?
set -e
printf '%s\n' "$runner_exit" >"$raw/runner.exit"
exit "$runner_exit"
