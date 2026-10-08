#!/bin/sh
set -eu
python /src/verify_contract.py --schema /src/event-schema.json --traces /src/trace-cases.json --out /out/VERIFICATION.json
python /src/audit_contract.py --traces /src/trace-cases.json --verification /out/VERIFICATION.json --out /out/AUDIT.json
