#!/bin/sh
set -eu
OUT=${1:-FORMAL_RESULT.json}
STATUS=${2:-FORMAL_EXIT.txt}
STDOUT=${3:-FORMAL_STDOUT.json}
STDERR=${4:-FORMAL_STDERR.txt}
[ ! -e "$OUT" ] || exit 17
[ ! -e "$STATUS" ] || exit 18
( python runner.py --out "$OUT" >"$STDOUT" 2>"$STDERR"; rc=$?; printf '%s\n' "$rc" >"$STATUS" ) &
printf '%s\n' "$!"
