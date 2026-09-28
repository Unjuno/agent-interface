# Audit construction record

Construction-only seeds: 600501/600502/600503. Formal experiment runner invocations: zero. The only planned formal invocation is a separate raw-only audit of #5198's already-retained result, verified by SHA-256 b55b8d9e58497c47ef5a2152d1236d27fdb6918a018cbeebf2a75f0b5f709470.

Before freezing, run the focused unit suite in the pinned Docker Desktop image. Retain exact Docker context/engine/image/container/exit and verify that all three construction seeds remain disjoint from the referenced #5198 seeds. Do not point construction tests at the formal raw.

## Construction invocation

Executed once in Docker Desktop context desktop-linux, Engine 28.5.1, linux/amd64, pinned image config digest sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a:

`docker --context desktop-linux run --cidfile <temp>/typed-mode-v5-posthoc-construction.cid --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m --mount type=bind,source=<audit-source>,target=/src,readonly --workdir /src python@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a python -B -m unittest -v test_construction.py`

Result: 3/3 tests passed; exit 0. Container 1102b7b76b60e9b5df59f3042cd7c1fe2de487d8a093b10945cdd158fe8fbe18 was inspected as exited/0 with the pinned image and removed. Docker Desktop running-container inventory was empty afterward. Tests used only construction seeds 600501/600502/600503; no formal raw was mounted and no formal audit was run.
