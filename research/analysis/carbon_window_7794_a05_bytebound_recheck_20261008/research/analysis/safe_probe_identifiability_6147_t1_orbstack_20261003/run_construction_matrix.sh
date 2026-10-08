#!/bin/sh
set -eu

PKG=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="$PKG/construction_smoke/run_10"
IMAGE='issue4466-gtk-pixel-stability@sha256:7c202113e519666007d7f6a74fa4a9854ed7cec62c07c1e80631474e69af7a27'
FIXTURE='ai6147-t1-matrix-fixture-v2-20261003'
OBSERVER='ai6147-t1-matrix-observer-v2-20261003'

if [ -e "$OUT" ]; then
    printf 'STOP_OUTPUT_PATH_EXISTS path=%s\n' "$OUT" >&2
    exit 64
fi
mkdir -p "$OUT/x11"
for name in "$FIXTURE" "$OBSERVER"; do
    if docker inspect "$name" >/dev/null 2>&1; then
        printf 'STOP_CONTAINER_NAME_EXISTS name=%s\n' "$name" >&2
        exit 65
    fi
done

docker run --pull=never --platform linux/arm64 --name "$FIXTURE" -d \
    --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL \
    --security-opt no-new-privileges \
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
    printf 'STOP_X11_SOCKET_NOT_READY\n' >&2
    exit 66
fi

set +e
docker run --pull=never --platform linux/arm64 --name "$OBSERVER" \
    --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
    --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL \
    --security-opt no-new-privileges \
    --mount "type=bind,src=$OUT/x11,dst=/tmp/.X11-unix,readonly" \
    --mount "type=bind,src=$PKG/construction_matrix_smoke.py,dst=/observer.py,readonly" \
    --mount "type=bind,src=$PKG/inputs/formal_01/deck_adaptive.jsonl,dst=/deck.jsonl,readonly" \
    --env DISPLAY=:99 --entrypoint python3 "$IMAGE" /observer.py \
    >"$OUT/transport.json" 2>"$OUT/observer.stderr"
observer_rc=$?
set -e
printf '%s\n' "$observer_rc" >"$OUT/observer.exit"
docker inspect "$OBSERVER" >"$OUT/observer.inspect.json" 2>/dev/null || true
docker rm "$OBSERVER" >/dev/null 2>&1 || true

running=$(docker inspect --format '{{.State.Running}}' "$FIXTURE" 2>/dev/null || true)
if [ "$running" = true ]; then
    docker stop --time 2 "$FIXTURE" >"$OUT/fixture.stop.stdout" 2>"$OUT/fixture.stop.stderr" || true
fi
docker inspect "$FIXTURE" >"$OUT/fixture.inspect.json" 2>/dev/null || true
docker logs "$FIXTURE" >"$OUT/oracle.jsonl" 2>"$OUT/fixture.logs.stderr" || true
docker cp "$FIXTURE:/tmp/xvfb.log" "$OUT/xvfb.log" >"$OUT/xvfb.cp.stdout" 2>"$OUT/xvfb.cp.stderr" || true
docker rm "$FIXTURE" >/dev/null 2>&1 || true
exit "$observer_rc"
