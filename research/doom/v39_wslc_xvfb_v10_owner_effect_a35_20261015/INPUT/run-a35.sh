#!/bin/bash
set -eu
RUNTIME=/mnt/d/codex-research/v39-xvfb-a09-env-20261012
SOURCE=/study/SOURCE
OUT=/study/OUTPUT/A35
cd "$SOURCE"
sha256sum -c SHA256SUMS.txt
export PATH="$RUNTIME/root/usr/bin:/usr/local/bin:/usr/bin:/bin"
export LD_LIBRARY_PATH="$RUNTIME/root/usr/lib/x86_64-linux-gnu"
export PYTHONPATH="$SOURCE:$RUNTIME/root/usr/lib/python3/dist-packages"
set +e
python3 "$SOURCE/candidate.py" --out "$OUT" --display :177
candidate_rc=$?
if [ -f "$OUT/RAW.json" ]; then
  PYTHONPATH="$SOURCE" python3 "$SOURCE/auditor.py" --raw "$OUT/RAW.json" --out "$OUT/AUDIT.json"
  audit_rc=$?
else
  audit_rc=98
fi
printf '{"candidate_exit":%s,"audit_exit":%s}\n' "$candidate_rc" "$audit_rc"
exit "$audit_rc"
