#!/bin/sh
set -eu
fail() { echo "PREFLIGHT_STOP:$1" >&2; exit 90; }
expected_archive='8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5'
expected_uid='501'
expected_gid='501'
expected_cpu='100000 100000'
expected_memory='1073741824'
expected_swap='0'
expected_pids='128'

actual_archive=$(sha256sum /input.tar | cut -d ' ' -f1)
echo "archive_sha256=$actual_archive"
[ "$actual_archive" = "$expected_archive" ] || fail archive_sha256
(cd /input && sha256sum -c /custody/input.SHA256) || fail input_hashes
actual_uid=$(id -u); actual_gid=$(id -g)
echo "uid=$actual_uid gid=$actual_gid"
[ "$actual_uid" = "$expected_uid" ] || fail uid
[ "$actual_gid" = "$expected_gid" ] || fail gid
for key in cpu.max memory.max memory.swap.max pids.max; do
  value=$(cat "/sys/fs/cgroup/$key")
  echo "cgroup.$key=$value"
done
[ "$(cat /sys/fs/cgroup/cpu.max)" = "$expected_cpu" ] || fail cpu.max
[ "$(cat /sys/fs/cgroup/memory.max)" = "$expected_memory" ] || fail memory.max
[ "$(cat /sys/fs/cgroup/memory.swap.max)" = "$expected_swap" ] || fail memory.swap.max
[ "$(cat /sys/fs/cgroup/pids.max)" = "$expected_pids" ] || fail pids.max
exec python3 -B /input/research/doom/v39_eof_formal_59_f03_20261004_3cbf/runner.py /output/data
