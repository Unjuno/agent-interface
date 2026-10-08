#!/bin/sh
set -eu

PKG=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RAW="$PKG/raw/formal_02"
IMAGE='issue4466-gtk-pixel-stability@sha256:7c202113e519666007d7f6a74fa4a9854ed7cec62c07c1e80631474e69af7a27'
ARMS='adaptive no_probe one_step'
CREATED=''

cleanup() {
    for name in $CREATED; do
        if docker inspect "$name" >/dev/null 2>&1; then
            running=$(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null || true)
            if [ "$running" = true ]; then
                docker stop --time 2 "$name" >/dev/null 2>&1 || true
            fi
        fi
    done
}
trap cleanup EXIT HUP INT TERM

if [ -e "$RAW" ]; then
    printf 'STOP_OUTPUT_PATH_EXISTS path=%s\n' "$RAW" >&2
    exit 64
fi
mkdir -p "$RAW"
for arm in $ARMS; do
    if [ -e "$RAW/$arm/candidate.jsonl" ] || [ -e "$RAW/$arm/oracle.jsonl" ]; then
        printf 'STOP_OUTPUT_PATH_EXISTS arm=%s\n' "$arm" >&2
        exit 65
    fi
    for suffix in fixture candidate; do
        name="ai6147-t2-a02-${arm}-${suffix}-20261003"
        if docker inspect "$name" >/dev/null 2>&1; then
            printf 'STOP_CONTAINER_NAME_EXISTS name=%s\n' "$name" >&2
            exit 66
        fi
    done
done

for arm in $ARMS; do
    mkdir -p "$RAW/$arm" "$RAW/$arm/x11"
    fixture="ai6147-t2-a02-${arm}-fixture-20261003"
    candidate="ai6147-t2-a02-${arm}-candidate-20261003"
    CREATED="$CREATED $fixture $candidate"

    docker run --pull=never --platform linux/arm64 --name "$fixture" -d \
        --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
        --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL \
        --security-opt no-new-privileges \
        --mount "type=bind,src=$RAW/$arm/x11,dst=/tmp/.X11-unix" \
        --mount "type=bind,src=$PKG/fixture.py,dst=/fixture.py,readonly" \
        --mount "type=bind,src=$PKG/inputs/formal_01/deck_${arm}.jsonl,dst=/deck.jsonl,readonly" \
        --entrypoint sh "$IMAGE" -c \
        'Xvfb :99 -screen 0 640x480x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 & exec python3 /fixture.py --deck /deck.jsonl' \
        >"$RAW/$arm/fixture.container-id" 2>"$RAW/$arm/fixture.start.stderr"

    ready=0
    for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
        if [ -S "$RAW/$arm/x11/X99" ]; then
            ready=1
            break
        fi
        running=$(docker inspect --format '{{.State.Running}}' "$fixture" 2>/dev/null || true)
        if [ "$running" != true ]; then
            break
        fi
        sleep 0.1
    done
    if [ "$ready" -ne 1 ]; then
        docker inspect "$fixture" >"$RAW/$arm/fixture.inspect.json" 2>/dev/null || true
        docker logs "$fixture" >"$RAW/$arm/oracle.jsonl" 2>"$RAW/$arm/fixture.logs.stderr" || true
        printf 'STOP_X11_SOCKET_NOT_READY arm=%s\n' "$arm" >&2
        exit 67
    fi

    set +e
    docker run --pull=never --platform linux/arm64 --name "$candidate" \
        --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
        --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL \
        --security-opt no-new-privileges \
        --mount "type=bind,src=$RAW/$arm/x11,dst=/tmp/.X11-unix,readonly" \
        --mount "type=bind,src=$PKG/candidate.py,dst=/candidate.py,readonly" \
        --mount "type=bind,src=$PKG/policy.py,dst=/policy.py,readonly" \
        --mount "type=bind,src=$PKG/lifecycle.py,dst=/lifecycle.py,readonly" \
        --mount "type=bind,src=$PKG/model.json,dst=/model.json,readonly" \
        --mount "type=bind,src=$PKG/inputs/formal_01/contexts_${arm}.jsonl,dst=/contexts.jsonl,readonly" \
        --env DISPLAY=:99 --entrypoint python3 "$IMAGE" \
        /candidate.py --arm "$arm" --model /model.json --contexts /contexts.jsonl \
        >"$RAW/$arm/candidate.jsonl" 2>"$RAW/$arm/candidate.stderr"
    candidate_rc=$?
    set -e
    printf '%s\n' "$candidate_rc" >"$RAW/$arm/candidate.exit"
    docker inspect "$candidate" >"$RAW/$arm/candidate.inspect.json" 2>/dev/null || true
    docker rm "$candidate" >/dev/null 2>&1 || true

    fixture_done=0
    for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
        running=$(docker inspect --format '{{.State.Running}}' "$fixture" 2>/dev/null || true)
        if [ "$running" != true ]; then
            fixture_done=1
            break
        fi
        sleep 0.1
    done
    if [ "$fixture_done" -ne 1 ]; then
        docker stop --time 2 "$fixture" >"$RAW/$arm/fixture.stop.stdout" 2>"$RAW/$arm/fixture.stop.stderr" || true
    fi
    docker inspect "$fixture" >"$RAW/$arm/fixture.inspect.json" 2>/dev/null || true
    docker logs "$fixture" >"$RAW/$arm/oracle.jsonl" 2>"$RAW/$arm/fixture.logs.stderr" || true
    docker cp "$fixture:/tmp/xvfb.log" "$RAW/$arm/xvfb.log" >"$RAW/$arm/xvfb.cp.stdout" 2>"$RAW/$arm/xvfb.cp.stderr" || true
    docker rm "$fixture" >/dev/null 2>&1 || true

    if [ "$candidate_rc" -ne 0 ] || [ "$fixture_done" -ne 1 ]; then
        printf 'STOP_FORMAL_ARM arm=%s candidate_exit=%s fixture_done=%s\n' "$arm" "$candidate_rc" "$fixture_done" >&2
        exit 68
    fi
done

auditor="ai6147-t2-a02-auditor-20261003"
if docker inspect "$auditor" >/dev/null 2>&1; then
    printf 'STOP_CONTAINER_NAME_EXISTS name=%s\n' "$auditor" >&2
    exit 69
fi
CREATED="$CREATED $auditor"
set +e
docker run --pull=never --platform linux/arm64 --name "$auditor" \
    --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
    --cpus 1 --memory 512m --pids-limit 64 --cap-drop ALL \
    --security-opt no-new-privileges \
    --mount "type=bind,src=$RAW,dst=/raw,readonly" \
    --mount "type=bind,src=$PKG/auditor.py,dst=/auditor.py,readonly" \
    --entrypoint python3 "$IMAGE" /auditor.py --root /raw \
    >"$RAW/AUDIT.json" 2>"$RAW/auditor.stderr"
auditor_rc=$?
set -e
printf '%s\n' "$auditor_rc" >"$RAW/auditor.exit"
docker inspect "$auditor" >"$RAW/auditor.inspect.json" 2>/dev/null || true
docker rm "$auditor" >/dev/null 2>&1 || true
if [ "$auditor_rc" -ne 0 ]; then
    printf 'STOP_AUDITOR_EXIT=%s\n' "$auditor_rc" >&2
    exit 70
fi
