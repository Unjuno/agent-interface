#!/bin/sh
set -u

ROOT=$(CDPATH= cd "$(dirname "$0")/.." && pwd) || exit 90
OUT="$ROOT/results/formal-t6-01/output"
HOST="$ROOT/results/formal-t6-01-host"
IMAGE='python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
IMAGE_ID='sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b'
NAME='audit-completion-5895-t6-amd64-candidate-8d0c7f53'

mkdir -p "$OUT" "$HOST" || exit 90
[ "$(docker context show 2>/dev/null)" = 'orbstack' ] || exit 91
[ -z "$(find "$OUT" -mindepth 1 -print -quit 2>/dev/null)" ] || exit 94
[ -z "$(find "$HOST" -mindepth 1 -print -quit 2>/dev/null)" ] || exit 95
IMAGE_INFO=$(docker image inspect --platform linux/amd64 --format '{{.Id}} {{.Os}}/{{.Architecture}}' "$IMAGE" 2>/dev/null) || exit 92
[ "$IMAGE_INFO" = "$IMAGE_ID linux/amd64" ] || exit 93
docker image inspect --platform linux/amd64 "$IMAGE" > "$HOST/prelaunch-image-inspect.json" 2> "$HOST/prelaunch-image-inspect.stderr" || exit 96
docker ps --no-trunc --format '{{json .}}' > "$HOST/prelaunch-running-containers.jsonl" 2> "$HOST/prelaunch-running-containers.stderr" || exit 97
[ ! -s "$HOST/prelaunch-running-containers.jsonl" ] || exit 98
EXISTING=$(docker ps -a --filter "name=^/${NAME}$" -q 2>/dev/null) || exit 99
[ -z "$EXISTING" ] || exit 100

docker run \
  --cidfile "$HOST/candidate.cid" \
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
  --mount "type=bind,source=$OUT,target=/out" \
  "$IMAGE" \
  python -B /study/source/candidate.py --target /study/source/target --out /out \
  >"$HOST/candidate.stdout" 2>"$HOST/candidate.stderr"
RC=$?
printf '%s\n' "$RC" > "$HOST/candidate.exit"
if [ -f "$HOST/candidate.cid" ]; then
  CID=$(sed -n '1p' "$HOST/candidate.cid")
  docker inspect "$CID" > "$HOST/candidate-container-inspect.json" 2> "$HOST/candidate-container-inspect.stderr"
  printf '%s\n' "$?" > "$HOST/candidate-inspect.exit"
fi
exit "$RC"
