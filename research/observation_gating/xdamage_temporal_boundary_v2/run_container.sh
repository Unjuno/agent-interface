#!/bin/sh
# Formal single-shot container launcher. Do not rerun the same allocation.
set -eu
IMAGE="agent-interface-gtk-preflight:local"
EXPECTED="sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4"
ACTUAL="$(docker image inspect "$IMAGE" --format '{{.Id}}')"
[ "$ACTUAL" = "$EXPECTED" ] || { echo "STOP_IMAGE_ID_MISMATCH expected=$EXPECTED actual=$ACTUAL" >&2; exit 20; }
OUT="${OUT:-$PWD/results/formal01}"
[ ! -e "$OUT" ] || { echo "STOP_OUTPUT_EXISTS $OUT" >&2; exit 21; }
SOURCE_GIT_COMMIT="$(git rev-parse HEAD)"
mkdir -p "$OUT"
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cpus 1 --memory 2g --pids-limit 64 --security-opt no-new-privileges --cap-drop ALL \
  -e SOURCE_GIT_COMMIT="$SOURCE_GIT_COMMIT" -v "$PWD:/src:ro" -v "$OUT:/results:rw" --entrypoint /bin/sh "$IMAGE" -ec '
    cd /src/research/observation_gating/xdamage_temporal_boundary_v2
    python3 -m unittest -v test_temporal_protocol.py
    python3 run_formal.py --mode formal --sessions 8 --out /results/formal
    runner_status=$?
    if [ "$runner_status" -ne 0 ]; then exit "$runner_status"; fi
    python3 audit_formal.py /results/formal --source-root .
  '
