set -u
out=/home/user/owned-parent-pidfd-watch-20261127-r01
mount -t tmpfs -o mode=1777 tmpfs /tmp || exit 90
cd /home/user/agent-durable-capacity-20261127 || exit 91
PYTHONPATH=. /home/user/.venvs/agent-interface-goal/bin/python "$out/experiment.py" > "$out/result.json" 2> "$out/stderr.log"
rc=$?
printf '%s\n' "$rc" > "$out/experiment-exit-code.txt"
exit "$rc"
