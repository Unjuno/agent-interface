#!/bin/bash
set -eu
umask 022

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
OUT="$SCRIPT_DIR/results/a01"
ENGINE=/Users/taka/.orbstack/bin/docker
IMAGE=issue59-sync-ack-loss-a01:e0013259
CONTAINER=issue59-sync-ack-loss-a01-e0013259

if [ -e "$OUT/RUN-STARTED" ]; then
    echo "refusing a second attempt: $OUT/RUN-STARTED exists" >&2
    exit 90
fi
if find "$OUT" -type f ! -name .gitkeep -print -quit | grep -q .; then
    echo "refusing non-fresh output directory: $OUT" >&2
    exit 91
fi
touch "$OUT/RUN-STARTED"

cat > "$OUT/COMMANDS.txt" <<EOF
candidate_source_commit=e00132595e0e801aabeae97ada53c580dfb11b9d
freeze_commit=$(git -C "$REPO_ROOT" rev-parse HEAD)
docker_cli=$ENGINE
host_uid=$(id -u)
host_gid=$(id -g)
build: $ENGINE build --pull --progress=plain --file $SCRIPT_DIR/Dockerfile --tag $IMAGE $SCRIPT_DIR
image_manifest: $ENGINE image inspect $IMAGE
create: $ENGINE create --name $CONTAINER --network none --memory 1073741824 --cpus 1 --pids-limit 64 --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=32m --cap-drop ALL --security-opt no-new-privileges --user $(id -u):$(id -g) --mount research/live_control:/workspace/research/live_control:ro --mount research/doom:/workspace/research/doom:ro --mount $OUT:/out:rw $IMAGE python -B /workspace/research/doom/issue_59_sync_ack_loss_linux_a01_20261007/run_tests.py
start: $ENGINE start --attach <container-id>
runtime_network=none
resource_limits=cpus=1,memory=1073741824,pids=64,read-only-rootfs,all-capabilities-dropped,no-new-privileges,tmpfs-/tmp-32MiB
host_preflight: $ENGINE version; $ENGINE info --format '{{json .DriverStatus}} {{.DockerRootDir}} {{.ServerVersion}}'; $ENGINE ps --format '{{.ID}} {{.Image}} {{.Names}}'; sysctl -n hw.memsize; memory_pressure -Q; df -h /
EOF

if "$ENGINE" version > "$OUT/HOST_DOCKER_VERSION.txt" 2> "$OUT/HOST_DOCKER_VERSION.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_DOCKER_VERSION\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi
if "$ENGINE" info --format '{{json .DriverStatus}} {{.DockerRootDir}} {{.ServerVersion}}' \
        > "$OUT/HOST_DOCKER_INFO.txt" 2> "$OUT/HOST_DOCKER_INFO.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_DOCKER_INFO\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi
if "$ENGINE" ps --format '{{.ID}} {{.Image}} {{.Names}}' \
        > "$OUT/HOST_CONTAINERS_BEFORE.txt" 2> "$OUT/HOST_CONTAINERS_BEFORE.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_DOCKER_PS\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi
if [ -s "$OUT/HOST_CONTAINERS_BEFORE.txt" ]; then
    printf 'status=HOLD_ACTIVE_CONTAINER\n' > "$OUT/RUN_STATUS.txt"
    exit 92
fi
if sysctl -n hw.memsize > "$OUT/HOST_MEMORY_BYTES.txt" 2> "$OUT/HOST_MEMORY.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_HOST_MEMORY\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi
if memory_pressure -Q > "$OUT/HOST_MEMORY_PRESSURE.txt" 2> "$OUT/HOST_MEMORY_PRESSURE.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_HOST_MEMORY_PRESSURE\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi
if df -h / > "$OUT/HOST_DISK.txt" 2> "$OUT/HOST_DISK.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_HOST_DISK\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi

if "$ENGINE" build --pull --progress=plain --file "$SCRIPT_DIR/Dockerfile" \
        --tag "$IMAGE" "$SCRIPT_DIR" > "$OUT/BUILD.log" 2>&1; then
    printf 'status=BUILD_PASS\n' > "$OUT/BUILD_STATUS.txt"
else
    status=$?
    printf 'status=STOP_BUILD\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi

if "$ENGINE" image inspect "$IMAGE" > "$OUT/IMAGE_MANIFEST.json" 2> "$OUT/IMAGE_INSPECT.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_IMAGE_INSPECT\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi

if cid=$("$ENGINE" create --name "$CONTAINER" --network none \
        --memory 1073741824 --cpus 1 --pids-limit 64 --read-only \
        --tmpfs /tmp:rw,nosuid,nodev,noexec,size=32m --cap-drop ALL \
        --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
        --mount "type=bind,src=$REPO_ROOT/research/live_control,dst=/workspace/research/live_control,readonly" \
        --mount "type=bind,src=$REPO_ROOT/research/doom,dst=/workspace/research/doom,readonly" \
        --mount "type=bind,src=$OUT,dst=/out" \
        "$IMAGE" python -B /workspace/research/doom/issue_59_sync_ack_loss_linux_a01_20261007/run_tests.py \
        2> "$OUT/CREATE.stderr"); then
    :
else
    status=$?
    printf 'status=STOP_CREATE\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi
printf '%s\n' "$cid" > "$OUT/CONTAINER_ID.txt"

if "$ENGINE" inspect "$cid" > "$OUT/CONTAINER_INSPECT_BEFORE.json" \
        2> "$OUT/CONTAINER_INSPECT_BEFORE.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_INSPECT_BEFORE\nexit_code=%s\n' "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi

set +e
"$ENGINE" start --attach "$cid" > "$OUT/CONTAINER_STDOUT.log" \
    2> "$OUT/CONTAINER_STDERR.log"
run_status=$?
set -e
printf '%s\n' "$run_status" > "$OUT/CONTAINER_EXIT_CODE.txt"

if "$ENGINE" inspect "$cid" > "$OUT/CONTAINER_INSPECT_AFTER.json" \
        2> "$OUT/CONTAINER_INSPECT_AFTER.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_INSPECT_AFTER\ncontainer_exit_code=%s\ninspect_exit_code=%s\n' \
        "$run_status" "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi

if "$ENGINE" rm "$cid" > "$OUT/CONTAINER_REMOVE.stdout" \
        2> "$OUT/CONTAINER_REMOVE.stderr"; then
    :
else
    status=$?
    printf 'status=STOP_CONTAINER_REMOVE\ncontainer_exit_code=%s\nremove_exit_code=%s\n' \
        "$run_status" "$status" > "$OUT/RUN_STATUS.txt"
    exit "$status"
fi

if [ "$run_status" -eq 0 ]; then
    printf 'status=RUN_PASS\ncontainer_exit_code=0\n' > "$OUT/RUN_STATUS.txt"
else
    printf 'status=FAIL_RUN\ncontainer_exit_code=%s\n' "$run_status" > "$OUT/RUN_STATUS.txt"
fi
exit "$run_status"
