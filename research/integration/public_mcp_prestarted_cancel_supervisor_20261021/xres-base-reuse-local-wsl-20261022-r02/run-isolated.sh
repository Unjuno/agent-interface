#!/usr/bin/env bash
set -euo pipefail
repo_root="$1"
packet="$2"
unshare --user --map-root-user --mount --fork bash -s -- "$repo_root" "$packet" <<'INNER'
set -euo pipefail
repo_root="$1"
packet="$2"
mount --make-rprivate /
mount -t tmpfs -o mode=1777 tmpfs /tmp
mkdir -m 1777 /tmp/.X11-unix
test "$(stat -c %a /tmp/.X11-unix)" = 1777
mountpoint -q /tmp
exec bash "$packet/run-probe.sh" "$repo_root" "$packet"
INNER
