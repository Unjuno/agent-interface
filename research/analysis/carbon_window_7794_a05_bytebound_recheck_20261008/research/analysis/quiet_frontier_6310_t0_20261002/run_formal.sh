#!/usr/bin/env bash
set -u

ROOT=/home/unjuno/research_6310_t0_v1
OUT="$ROOT/formal_output"
WSLC='/mnt/c/Program Files/WSL/wslc.exe'
IMAGE='python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
mkdir -p "$OUT"

sha256sum -c "$ROOT/SOURCE_SHA256SUMS.txt" > "$OUT/source_integrity.txt" 2> "$OUT/source_integrity_stderr.txt"
integrity_exit=$?
printf '%s\n' "$integrity_exit" > "$OUT/source_integrity_exit.txt"
if [ "$integrity_exit" -ne 0 ]; then
  printf 'SKIPPED_SOURCE_INTEGRITY_FAILURE\n' > "$OUT/candidate_exit.txt"
  printf 'SKIPPED_SOURCE_INTEGRITY_FAILURE\n' > "$OUT/audit_exit.txt"
  exit 0
fi

"$WSLC" run --rm --name ai-6310-candidate-01 --pull never --network none --cpus 1 --memory 512M \
  --volume "$ROOT:/src:ro" --volume "$OUT:/out:rw" --workdir /src \
  "$IMAGE" python -B candidate.py /src/fixture.json > "$OUT/candidate_raw.json" 2> "$OUT/candidate_stderr.txt"
candidate_exit=$?
printf '%s\n' "$candidate_exit" > "$OUT/candidate_exit.txt"

if [ "$candidate_exit" -eq 0 ]; then
  "$WSLC" run --rm --name ai-6310-auditor-01 --pull never --network none --cpus 1 --memory 512M \
    --volume "$ROOT:/src:ro" --volume "$OUT:/out:rw" --workdir /src \
    "$IMAGE" python -B auditor.py /src/fixture.json /out/candidate_raw.json > "$OUT/audit_raw.json" 2> "$OUT/audit_stderr.txt"
  audit_exit=$?
  printf '%s\n' "$audit_exit" > "$OUT/audit_exit.txt"
else
  printf 'SKIPPED_CANDIDATE_NONZERO\n' > "$OUT/audit_exit.txt"
fi

"$WSLC" container list --all > "$OUT/container_list_after.txt" 2> "$OUT/container_list_stderr.txt"
