#!/usr/bin/env bash
set -uo pipefail

packet=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/repository-cleanup-plan-r01-20261020/research/integration/chromium_public_compiled_caller_20261021
repo=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/repository-cleanup-plan-r01-20261020
display_id=:95
site_packages=/home/user/.cache/agent-interface-xvfb-current-e7-r02/lib/python3.12/site-packages
export DISPLAY="$display_id"
export PYTHONPATH="$repo:$site_packages"

Xvfb "$display_id" -screen 0 1024x768x24 -ac -nolisten tcp >"$packet/raw/xvfb-r02.log" 2>&1 &
xvfb_pid=$!
xvfb_cmdline=''
xvfb_exit_status=null

cleanup() {
    set +e
    if kill -0 "$xvfb_pid" 2>/dev/null; then
        kill -TERM "$xvfb_pid" 2>/dev/null
    fi
    wait "$xvfb_pid"
    xvfb_status=$?
    xvfb_exit_status=$xvfb_status
    if kill -0 "$xvfb_pid" 2>/dev/null; then
        kill -KILL "$xvfb_pid" 2>/dev/null
        wait "$xvfb_pid"
        xvfb_status=$?
        xvfb_exit_status=$xvfb_status
    fi
    printf '{"display":":95","pid":%s,"cmdline":"%s","exit_status":%s,"reaped":true}\n' \
        "$xvfb_pid" "$xvfb_cmdline" "$xvfb_exit_status" >"$packet/raw/xvfb-lifecycle-r02.json"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for attempt in $(seq 1 50); do
    if ! kill -0 "$xvfb_pid" 2>/dev/null; then
        echo "owned Xvfb exited before readiness" >&2
        exit 2
    fi
    if DISPLAY="$display_id" PYTHONPATH="$PYTHONPATH" python3.12 -c \
        'from Xlib import display; d=display.Display(":95"); s=d.screen(); assert (s.width_in_pixels,s.height_in_pixels)==(1024,768); d.close()' \
        >/dev/null 2>&1; then
        break
    fi
    sleep 0.1
done

if ! DISPLAY="$display_id" PYTHONPATH="$PYTHONPATH" python3.12 -c \
    'from Xlib import display; d=display.Display(":95"); s=d.screen(); assert (s.width_in_pixels,s.height_in_pixels)==(1024,768); d.close()' \
    >/dev/null 2>&1; then
    echo "owned Xvfb did not provide the frozen display geometry" >&2
    exit 3
fi

xvfb_cmdline=$(tr '\0' ' ' <"/proc/$xvfb_pid/cmdline")
case "$xvfb_cmdline" in
    *"Xvfb :95 -screen 0 1024x768x24"*) ;;
    *) echo "Xvfb PID does not match the frozen private display command" >&2; exit 4 ;;
esac

set +e
python3.12 "$packet/run_public_caller_r02.py" >"$packet/raw/runner-console-r02.log" 2>&1
runner_status=$?
set -e
exit "$runner_status"
