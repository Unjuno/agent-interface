# Construction record — allocation -01

Frozen intake main: `317071858f3bc9e0d3d90330095b90c9835dc591`. Formal seeds 67010231/67010232/67010233 are reserved for the single formal runner and must not be used in construction. Construction-only seeds are 550503/550504/550505.

The construction suite checks deterministic sample generation and output, balanced modes/blocks, independent audit reconstruction, matched-threshold derivation and 16 corruption-rejection controls using only construction seeds and 20 rows/block. Construction is not a formal result. Record the exact Docker command, image identity, container ID, exit status and test counts below before formal freeze.

## Construction invocation

Executed once in Docker Desktop context `desktop-linux`, Engine 28.5.1, Linux x86_64, pinned image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`. Command:

```text
docker --context desktop-linux run --cidfile <temp>/typed-mode-v5-construction.cid --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m --mount type=bind,source=<experiment-directory>,target=/src,readonly --workdir /src python@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a python -B -m unittest -v test_construction.py
```

Result: 3/3 tests passed; exit 0. Container `e34f7559f06d77b629dd6ef47151b79d4cf8f889abb0e3e0fff69f27ca18fc84` was inspected as exited/0 with the pinned image and removed. Docker Desktop running-container inventory was empty afterward. Tests used only construction seeds 550503/550504/550505 and 20 rows/block; no formal seed was accessed and no formal runner/auditor was started.
