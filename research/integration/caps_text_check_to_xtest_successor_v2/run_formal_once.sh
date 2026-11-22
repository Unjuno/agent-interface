#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: run_formal_once.sh REPOSITORY_ROOT FROZEN_COMMIT NEW_RUN_ROOT" >&2
  exit 64
fi

repo=$(cd "$1" && pwd)
freeze_commit=$2
run_root=$3
study="$repo/research/integration/caps_text_check_to_xtest_successor_v2"

if [[ -e "$run_root" ]]; then
  echo "STOP: run root already exists; no overwrite or rerun" >&2
  exit 65
fi

# Every formal process, X server, fixture and IPC actor runs without a network
# interface or route. Source and package acquisition must finish beforehand.
exec sudo -n unshare --net -- python3 -B "$study/run_formal.py" \
  --repo "$repo" --freeze-commit "$freeze_commit" --out "$run_root"
