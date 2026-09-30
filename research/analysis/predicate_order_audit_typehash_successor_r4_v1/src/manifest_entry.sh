#!/bin/sh
set +e
python -B /src/manifest_probe.py > /audit/manifest.stdout 2> /audit/manifest.stderr
rc=$?
printf '%s\n' "$rc" > /audit/manifest.exit
exit "$rc"
