#!/bin/sh
set -u

ROOT=$(CDPATH= cd "$(dirname "$0")/.." && pwd) || exit 90
OUT="$ROOT/results/formal-t6-01/output"
HOST="$ROOT/results/formal-t6-01-host"
IMAGE='python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
IMAGE_ID='sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b'
NAME='audit-completion-5895-t6-amd64-independent-audit-8d0c7f53'

[ -f "$HOST/candidate.exit" ] || exit 90
[ "$(sed -n '1p' "$HOST/candidate.exit")" = '0' ] || exit 91
[ -f "$HOST/candidate.cid" ] || exit 92
[ -f "$HOST/candidate-container-inspect.json" ] || exit 93
[ -f "$HOST/candidate-inspect.exit" ] || exit 94
[ "$(sed -n '1p' "$HOST/candidate-inspect.exit")" = '0' ] || exit 95
[ -f "$HOST/candidate.stdout" ] || exit 96
[ -f "$HOST/candidate.stderr" ] || exit 97
[ -f "$OUT/candidate_manifest.json" ] || exit 98
[ "$(docker context show 2>/dev/null)" = 'orbstack' ] || exit 99
IMAGE_INFO=$(docker image inspect --platform linux/amd64 --format '{{.Id}} {{.Os}}/{{.Architecture}}' "$IMAGE" 2>/dev/null) || exit 100
[ "$IMAGE_INFO" = "$IMAGE_ID linux/amd64" ] || exit 104
docker image inspect --platform linux/amd64 "$IMAGE" > "$HOST/auditor-prelaunch-image-inspect.json" 2> "$HOST/auditor-prelaunch-image-inspect.stderr" || exit 105
docker ps --no-trunc --format '{{json .}}' > "$HOST/auditor-prelaunch-running-containers.jsonl" 2> "$HOST/auditor-prelaunch-running-containers.stderr" || exit 106
[ ! -s "$HOST/auditor-prelaunch-running-containers.jsonl" ] || exit 107
[ ! -e "$HOST/auditor.cid" ] || exit 102
EXISTING=$(docker ps -a --filter "name=^/${NAME}$" -q 2>/dev/null) || exit 108
[ -z "$EXISTING" ] || exit 109

docker run \
  --cidfile "$HOST/auditor.cid" \
  --name "$NAME" \
  --pull=never \
  --platform linux/amd64 \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m,uid=501,gid=20 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --cpus 1 \
  --memory 512m \
  --pids-limit 64 \
  --user 501:20 \
  --mount "type=bind,source=$ROOT/source,target=/study/source,readonly" \
  --mount "type=bind,source=$OUT,target=/out,readonly" \
  "$IMAGE" \
  python -B /study/source/independent_audit.py /out/candidate_manifest.json /study/source/target \
  >"$HOST/auditor.stdout" 2>"$HOST/auditor.stderr"
RC=$?
printf '%s\n' "$RC" > "$HOST/auditor.exit"
if [ -f "$HOST/auditor.cid" ]; then
  CID=$(sed -n '1p' "$HOST/auditor.cid")
  docker inspect "$CID" > "$HOST/auditor-container-inspect.json" 2> "$HOST/auditor-container-inspect.stderr"
  printf '%s\n' "$?" > "$HOST/auditor-inspect.exit"
fi
exit "$RC"
