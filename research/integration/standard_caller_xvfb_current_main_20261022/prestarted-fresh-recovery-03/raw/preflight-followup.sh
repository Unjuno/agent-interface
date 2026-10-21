#!/usr/bin/env bash
set -eu
ROOT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/goal-currentmain-recovery-20261022
DEPS=/home/user/.cache/agent-interface-codex-deps-20261022-r02
MANIFEST="$ROOT/research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02/raw/runtime-manifest.sha256"
. /etc/os-release
printf 'distribution=%s %s\n' "$NAME" "$VERSION_ID"
printf 'kernel=%s\n' "$(uname -r)"
printf 'python=%s\n' "$(python3 --version 2>&1)"
printf 'xvfb='; dpkg-query -W -f='${Version}\n' xvfb
printf 'xvfb_sha256='; sha256sum /usr/bin/Xvfb | cut -d' ' -f1
printf 'dependency_cache_exists='; test -d "$DEPS" && echo yes
PYTHONPATH="$DEPS" python3 - <<'PY'
from importlib.metadata import version
for package in ('python-xlib','Pillow','numpy','mcp'):
 print(f'{package}={version(package)}')
PY
printf 'xvfb_processes='; pgrep -af '[X]vfb' || true
printf 'runtime_source_hash_comparison:\n'
while read -r expected path; do actual=$(sha256sum "$ROOT/$path" | cut -d' ' -f1); printf '%s %s %s\n' "$path" "$expected" "$actual"; test "$expected" = "$actual"; done < "$MANIFEST"
printf 'private_namespace_mount_probe:\n'
unshare --user --map-root-user --mount --fork bash -ceu 'mount --make-rprivate /; mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp/.X11-unix; stat -c "%a %U:%G %n" /tmp/.X11-unix; test ! -S /tmp/.X11-unix/X88; echo display_88_free=yes'
