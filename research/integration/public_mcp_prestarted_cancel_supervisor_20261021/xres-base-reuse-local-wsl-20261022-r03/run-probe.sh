#!/usr/bin/env bash
set -u
repo_root="$1"
packet="$2"
mkdir -p "$packet"
cd "$repo_root"
server89=""
server90=""
cleanup() {
  if [[ -n "$server89" ]]; then kill "$server89" 2>/dev/null || true; wait "$server89" 2>/dev/null || true; fi
  if [[ -n "$server90" ]]; then kill "$server90" 2>/dev/null || true; wait "$server90" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM
Xvfb :89 -screen 0 640x480x24 -nolisten tcp >"$packet/xvfb-89.log" 2>&1 &
server89=$!
Xvfb :90 -screen 0 640x480x24 -nolisten tcp >"$packet/xvfb-90.log" 2>&1 &
server90=$!
for display in :89 :90; do
  ready=0
  for _ in $(seq 1 100); do
    if DISPLAY="$display" python3 -c 'from Xlib.display import Display; d=Display(); d.close()' >/dev/null 2>&1; then ready=1; break; fi
    sleep 0.05
  done
  if [[ "$ready" != 1 ]]; then echo "Xvfb failed to become ready: $display" >&2; exit 2; fi
done
{
  date --iso-8601=seconds
  uname -a
  python3 --version
  python3 -c 'import Xlib; print("python-xlib", Xlib.__version__)'
  git rev-parse HEAD
  git status --short
  printf 'private_mount_namespace=required\ninput_events=0\nscenarios=observer_after_owner_exit;replacement_client_before_observer\n'
} >"$packet/conditions.txt"
git diff -- runtime/cli_v1/owned_guarded_session.py runtime/cli_v1/test_mcp_owned_process.py >"$packet/runtime.patch.txt"
PYTHONPATH="$repo_root" python3 "$packet/probe.py" >"$packet/probe.stdout.log" 2>"$packet/probe.stderr.log"
status=$?
cleanup
server89=""
server90=""
printf '%s\n' "$status" >"$packet/exit_code.txt"
sha256sum \
  "$packet/conditions.txt" "$packet/probe.py" "$packet/run-probe.sh" \
  "$packet/run-isolated.sh" "$packet/runtime.patch.txt" \
  "$packet/probe.stdout.log" "$packet/probe.stderr.log" \
  "$packet/result.json" "$packet/xvfb-89.log" "$packet/xvfb-90.log" \
  "$packet/exit_code.txt" \
  "$repo_root/runtime/guarded_x11_v1/cancel_supervisor.py" \
  "$repo_root/runtime/guarded_x11_v1/xres_client_fence.py" \
  "$repo_root/runtime/cli_v1/owned_guarded_session.py" \
  >"$packet/SHA256SUMS"
exit "$status"

