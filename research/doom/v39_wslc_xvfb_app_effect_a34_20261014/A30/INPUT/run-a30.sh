#!/bin/bash
set -u
RUNTIME=/mnt/d/codex-research/v39-xvfb-a09-env-20261012
SOURCE=/study/SOURCE
OUT=/study/OUTPUT/A30
ip link set lo up
ln -s "$RUNTIME/root/usr/bin/xkbcomp" /usr/bin/xkbcomp
cleanup() { rm -f /usr/bin/xkbcomp; }
trap cleanup EXIT
cd "$SOURCE"
sha256sum -c SHA256SUMS.txt || exit 90
export PATH="$RUNTIME/root/usr/bin:/usr/bin:/bin"
export LD_LIBRARY_PATH="$RUNTIME/root/usr/lib/x86_64-linux-gnu"
export PYTHONPATH="$SOURCE:$RUNTIME/root/usr/lib/python3/dist-packages"
set +e
su -s /bin/bash user -c "env PATH='$PATH' LD_LIBRARY_PATH='$LD_LIBRARY_PATH' PYTHONPATH='$PYTHONPATH' /usr/bin/python3 '$SOURCE/candidate.py' --out '$OUT' --display 127.0.0.1:143"
candidate_rc=$?
if [ -f "$OUT/RAW.json" ]; then
  su -s /bin/bash user -c "env PYTHONPATH='$SOURCE' /usr/bin/python3 '$SOURCE/auditor.py' --raw '$OUT/RAW.json' --out '$OUT/AUDIT.json'"
  audit_rc=$?
else
  audit_rc=98
fi
printf '{"candidate_exit":%s,"audit_exit":%s}\n' "$candidate_rc" "$audit_rc"
exit "$audit_rc"