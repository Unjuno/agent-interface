#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGE="sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
STAGE="${1:?usage: run_t0.sh construction|candidate|audit}"
BASE="$ROOT/formal/$STAGE"
NAME="blackwell-6678-t0-${STAGE}-20261002"

case "$STAGE" in
  construction)
    CMD=(python -B -m unittest discover -s /src -p 'test_*.py' -v)
    ;;
  candidate)
    CMD=(python -B /src/candidate.py /src/fixture.json /out/candidate.json)
    ;;
  audit)
    CMD=(python -B /src/auditor.py /src/fixture.json /in/candidate.json /out/audit.json)
    ;;
  *) echo "invalid stage" >&2; exit 64 ;;
esac

if [[ -e "$BASE.started" || -e "$BASE.exit" || -e "$BASE.stdout.log" || -e "$BASE.container-inspect.json" || -e "$BASE.cid" ]]; then
  echo "stage already has invocation evidence; refusing to run" >&2
  exit 73
fi
if [[ "$STAGE" == candidate && -e "$BASE/out/candidate.json" ]]; then
  echo "candidate output already exists; refusing to run" >&2
  exit 73
fi
if [[ "$STAGE" == audit && ( ! -s "$ROOT/formal/candidate/out/candidate.json" || -e "$BASE/out/audit.json" ) ]]; then
  echo "audit input missing or output already exists; refusing to run" >&2
  exit 73
fi

mkdir -p "$BASE/out"
touch "$BASE.started"
RUN_ARGS=(--name "$NAME" --cidfile "$BASE.cid" --network none --read-only
  --cap-drop ALL --security-opt no-new-privileges --user 65534:65534
  --cpus 0.25 --memory 256m --pids-limit 32
  --mount "type=bind,src=$ROOT,dst=/src,readonly"
  --mount "type=bind,src=$BASE/out,dst=/out")
if [[ "$STAGE" == audit ]]; then
  RUN_ARGS+=(--mount "type=bind,src=$ROOT/formal/candidate/out,dst=/in,readonly")
fi
docker run "${RUN_ARGS[@]}" "$IMAGE" "${CMD[@]}" >"$BASE.stdout.log" 2>&1
status=$?
printf '%s\n' "$status" > "$BASE.exit"
if [[ -s "$BASE.cid" ]]; then
  docker inspect "$(<"$BASE.cid")" > "$BASE.container-inspect.json"
fi
exit "$status"
