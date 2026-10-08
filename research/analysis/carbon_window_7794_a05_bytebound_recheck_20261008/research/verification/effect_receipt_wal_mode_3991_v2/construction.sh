#!/bin/sh
set -eu
mkdir -p /out/construction
python /src/runner.py --run /out/construction/raw /out/construction --construction
python /src/audit.py --result /out/construction/RESULT.json --raw-root /out/construction/raw --out /out/construction/AUDIT.json
(cd /out/construction && python /src/test_audit.py)
