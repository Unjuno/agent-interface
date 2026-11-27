#!/usr/bin/env bash
set -eu
ROOT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/goal-currentmain-recovery-20261022
RAW="$ROOT/research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/raw"
DEPS=/home/user/.cache/agent-interface-codex-deps-20261022-r02
. /etc/os-release
test "$VERSION_ID" = 24.04
test "$(python3 -c 'import sys; print(".".join(map(str,sys.version_info[:3])))')" = 3.12.3
test "$(dpkg-query -W -f='${Version}' xvfb)" = '2:21.1.12-1ubuntu1.8'
test -d "$DEPS"
if pgrep -x Xvfb >/dev/null; then echo preexisting_Xvfb_found >&2; exit 41; fi
PYTHONPATH="$DEPS" python3 - <<'PY' > "$RAW/dependency-versions.txt"
from importlib.metadata import version
expected={'python-xlib':'0.33','Pillow':'10.2.0','numpy':'1.26.4','mcp':'1.30.0'}
actual={name:version(name) for name in expected}
print(actual)
if actual != expected: raise SystemExit(f'dependency mismatch: {actual}')
PY
sha256sum /usr/bin/Xvfb > "$RAW/xvfb-binary.sha256"
command -v timeout > "$RAW/timeout-executable.txt"
python3 - "$ROOT" "$RAW/candidate-runtime-manifest.sha256" <<'PY'
import hashlib,sys
from pathlib import Path
root=Path(sys.argv[1]); manifest=Path(sys.argv[2]); bad=[]
for line in manifest.read_text().splitlines():
 expected,name=line.split('  ',1); actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
 print(f'{name} match={actual==expected}')
 if actual != expected: bad.append(name)
if bad: raise SystemExit(f'source mismatch: {bad}')
PY
unshare --user --map-root-user --mount --fork bash -ceu 'mount --make-rprivate /; mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp/.X11-unix; stat -c "%a %U:%G %n" /tmp/.X11-unix' > "$RAW/private-mount-probe.txt"
printf 'preflight=PASS\nmain=cc5ef16c560cc985ee0951d3d53d659e892f5167\n' > "$RAW/preflight-status.txt"