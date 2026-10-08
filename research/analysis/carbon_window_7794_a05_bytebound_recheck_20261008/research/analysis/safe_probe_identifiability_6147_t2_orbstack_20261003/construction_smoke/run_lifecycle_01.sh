#!/bin/sh
set -eu
PKG=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT="$PKG/construction_smoke/lifecycle_run_01"
IMAGE='issue4466-gtk-pixel-stability@sha256:7c202113e519666007d7f6a74fa4a9854ed7cec62c07c1e80631474e69af7a27'
FIXTURE='ai6147-t2-construction-fixture-20261003'
CANDIDATE='ai6147-t2-construction-candidate-20261003'
if [ -e "$OUT" ]; then printf 'STOP_OUTPUT_PATH_EXISTS path=%s\n' "$OUT" >&2; exit 64; fi
for name in "$FIXTURE" "$CANDIDATE"; do
    if docker inspect "$name" >/dev/null 2>&1; then printf 'STOP_CONTAINER_NAME_EXISTS name=%s\n' "$name" >&2; exit 65; fi
done
mkdir -p "$OUT/x11"
docker run --pull=never --platform linux/arm64 --name "$FIXTURE" -d \
    --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges \
    --mount "type=bind,src=$OUT/x11,dst=/tmp/.X11-unix" \
    --mount "type=bind,src=$PKG/fixture.py,dst=/fixture.py,readonly" \
    --mount "type=bind,src=$PKG/inputs/formal_01/deck_adaptive.jsonl,dst=/deck.jsonl,readonly" \
    --entrypoint sh "$IMAGE" -c \
    'Xvfb :99 -screen 0 640x480x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 & exec python3 /fixture.py --deck /deck.jsonl' \
    >"$OUT/fixture.container-id" 2>"$OUT/fixture.start.stderr"
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    if [ -S "$OUT/x11/X99" ]; then ready=1; break; fi
    running=$(docker inspect --format '{{.State.Running}}' "$FIXTURE" 2>/dev/null || true)
    if [ "$running" != true ]; then break; fi
    sleep 0.1
done
if [ "$ready" -ne 1 ]; then
    docker logs "$FIXTURE" >"$OUT/oracle.jsonl" 2>"$OUT/fixture.logs.stderr" || true
    docker inspect "$FIXTURE" >"$OUT/fixture.inspect.json" 2>/dev/null || true
    printf 'STOP_X11_SOCKET_NOT_READY\n' >&2; exit 66
fi
set +e
docker run --pull=never --platform linux/arm64 --name "$CANDIDATE" \
    --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
    --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges \
    --mount "type=bind,src=$OUT/x11,dst=/tmp/.X11-unix,readonly" \
    --mount "type=bind,src=$PKG/candidate.py,dst=/candidate.py,readonly" \
    --mount "type=bind,src=$PKG/policy.py,dst=/policy.py,readonly" \
    --mount "type=bind,src=$PKG/lifecycle.py,dst=/lifecycle.py,readonly" \
    --mount "type=bind,src=$PKG/model.json,dst=/model.json,readonly" \
    --mount "type=bind,src=$PKG/inputs/formal_01/contexts_adaptive.jsonl,dst=/contexts.jsonl,readonly" \
    --env DISPLAY=:99 --entrypoint python3 "$IMAGE" \
    /candidate.py --arm adaptive --model /model.json --contexts /contexts.jsonl \
    >"$OUT/candidate.jsonl" 2>"$OUT/candidate.stderr"
candidate_rc=$?
set -e
printf '%s\n' "$candidate_rc" >"$OUT/candidate.exit"
docker inspect "$CANDIDATE" >"$OUT/candidate.inspect.json" 2>/dev/null || true
docker rm "$CANDIDATE" >/dev/null 2>&1 || true
docker inspect "$FIXTURE" >"$OUT/fixture.inspect.json" 2>/dev/null || true
docker logs "$FIXTURE" >"$OUT/oracle.jsonl" 2>"$OUT/fixture.logs.stderr" || true
docker cp "$FIXTURE:/tmp/xvfb.log" "$OUT/xvfb.log" >"$OUT/xvfb.cp.stdout" 2>"$OUT/xvfb.cp.stderr" || true
docker rm "$FIXTURE" >/dev/null 2>&1 || true
if [ "$candidate_rc" -ne 0 ]; then printf 'STOP_CANDIDATE_EXIT=%s\n' "$candidate_rc" >&2; exit 67; fi
