#!/usr/bin/env bash
set -eu
ROOT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/goal-currentmain-recovery-20261022
RAW="$ROOT/research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01/raw"
DEPS=/home/user/.cache/agent-interface-codex-deps-20261022-r02
mount --make-rprivate /
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp/.X11-unix
stat -c '%a %U:%G %n' /tmp/.X11-unix > "$RAW/preflight-private-socket.txt"
test ! -S /tmp/.X11-unix/X88
if pgrep -x Xvfb >/dev/null; then echo preexisting_Xvfb_found >&2; exit 41; fi
. /etc/os-release
test "$VERSION_ID" = 24.04
test "$(python3 -c 'import sys; print(".".join(map(str,sys.version_info[:3])))')" = 3.12.3
test "$(dpkg-query -W -f='${Version}' xvfb)" = '2:21.1.12-1ubuntu1.8'
test -d "$DEPS"
PYTHONPATH="$DEPS" python3 - <<'PY'
from importlib.metadata import version
expected={'python-xlib':'0.33','Pillow':'10.2.0','numpy':'1.26.4','mcp':'1.30.0'}
actual={name:version(name) for name in expected}
print(actual)
if actual != expected: raise SystemExit(f'dependency mismatch: {actual}')
PY
sha256sum /usr/bin/Xvfb > "$RAW/preflight-xvfb-binary.sha256"
python3 - "$ROOT" "$RAW/candidate-runtime-manifest.sha256" <<'PY'
import hashlib,sys
from pathlib import Path
root=Path(sys.argv[1]); manifest=Path(sys.argv[2]); failures=[]
for line in manifest.read_text().splitlines():
 expected,path=line.split('  ',1); actual=hashlib.sha256((root/path).read_bytes()).hexdigest()
 print(f'{path} match={actual==expected}')
 if actual != expected: failures.append(path)
if failures: raise SystemExit(f'source hash mismatch: {failures}')
PY
printf 'preflight=PASS\nsource_sha=a85868f5deb36616db972b83edb591593db6986f\n' > "$RAW/preflight-status.txt"