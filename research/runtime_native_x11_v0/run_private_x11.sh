#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 2 ]; then echo "usage: $0 OUT DISPLAY" >&2; exit 2; fi
OUT=$1; DISPLAY_NUM=$2
if [ -e "$OUT" ]; then echo "refusing existing output: $OUT" >&2; exit 3; fi
mkdir -p "$OUT/bin"
root=$(cd "$(dirname "$0")" && pwd)
cd "$root"
GOPROXY=off GOSUMDB=off go build -o "$OUT/bin/fixture" ./cmd/fixture
GOPROXY=off GOSUMDB=off go build -o "$OUT/bin/controller" ./cmd/controller
GOPROXY=off GOSUMDB=off go build -o "$OUT/bin/score" ./cmd/score
Xvfb "$DISPLAY_NUM" -screen 0 800x600x24 -nolisten tcp >"$OUT/xvfb.stdout.txt" 2>"$OUT/xvfb.stderr.txt" &
xpid=$!
cleanup(){ kill "$xpid" 2>/dev/null || true; wait "$xpid" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 100); do DISPLAY="$DISPLAY_NUM" xdpyinfo >/dev/null 2>&1 && break; sleep .02; done
DISPLAY="$DISPLAY_NUM" xdpyinfo >"$OUT/xdpyinfo.txt"
run_condition(){
  local cond=$1
  DISPLAY="$DISPLAY_NUM" "$OUT/bin/fixture" --ready "$OUT/$cond.ready" --ledger "$OUT/$cond.ledger.jsonl" >"$OUT/$cond.fixture.stdout.txt" 2>"$OUT/$cond.fixture.stderr.txt" &
  local fp=$!
  for _ in $(seq 1 100); do [ -s "$OUT/$cond.ready" ] && break; sleep .02; done
  test -s "$OUT/$cond.ready"
  DISPLAY="$DISPLAY_NUM" "$OUT/bin/controller" --condition "$cond" --ready "$OUT/$cond.ready" --out "$OUT/$cond.receipt.json"
  if [ "$cond" = valid ]; then for _ in $(seq 1 100); do ! kill -0 "$fp" 2>/dev/null && break; sleep .02; done; fi
  kill "$fp" 2>/dev/null || true
  wait "$fp" 2>/dev/null || true
}
run_condition stale
run_condition expired
run_condition unsupported_text
run_condition valid
"$OUT/bin/score" \
  --valid-ledger "$OUT/valid.ledger.jsonl" --stale-ledger "$OUT/stale.ledger.jsonl" \
  --expired-ledger "$OUT/expired.ledger.jsonl" --unsupported-ledger "$OUT/unsupported_text.ledger.jsonl" \
  --valid-receipt "$OUT/valid.receipt.json" --stale-receipt "$OUT/stale.receipt.json" \
  --expired-receipt "$OUT/expired.receipt.json" --unsupported-receipt "$OUT/unsupported_text.receipt.json" \
  --out "$OUT/score.json"
python3 - "$OUT/score.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
raise SystemExit(0 if x.get('passed') is True else 1)
PY
