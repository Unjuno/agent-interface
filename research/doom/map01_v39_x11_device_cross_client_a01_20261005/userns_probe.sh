#!/usr/bin/env bash
set -u
t=/home/user/x11-xtest-device-cross-client-a01-20261005/setup/userns-mount-test
mkdir -p "$t"
unshare --user --map-root-user --mount sh -c 'id; mount -t tmpfs -o mode=1777 tmpfs "$1"; stat -c "%a %u %g %n" "$1"; umount "$1"; echo USERNS_PRIVATE_MOUNT_PASS' _ "$t"
rc=$?
rmdir "$t" 2>/dev/null || true
exit "$rc"
