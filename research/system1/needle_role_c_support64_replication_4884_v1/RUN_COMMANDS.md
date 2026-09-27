# Issue #4884 execution record

Frozen before formal allocation. Image `needle-pilot05:local`, ID `sha256:6ab7a93188ddf4232a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (Linux/amd64 CPU); offline; read-only source/root; 1 CPU; 2 GiB; 64 PIDs. Dedicated fresh volume `unjuno-needle-role-c-support64-replication-4884-v1`.

## Zero-update construction

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<frozen-source>,target=/src,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEED=7867401 -e NEEDLE_OUTPUT=/unused -e NEEDLE_SEEDS=7867401,7867601,7867801 --entrypoint python needle-pilot05:local /src/construction_test.py
```

Result: `CONSTRUCTION_PASS seeds=3 prefix_exact=True streams_disjoint=True byte_sentinel=True corruption_rejected=True optimizer_updates=0`.

## Wrapper import smoke (no training)

The frozen paired wrapper was invoked with `NEEDLE_OUTPUT=/src`, an existing non-empty read-only source directory. It successfully imported the upstream module and reached its intentional `STOP_ALLOCATION_OR_OUTPUT` assertion before any optimizer update. This checks the exact former failure boundary without entering formal training.

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<frozen-source>,target=/src,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEED=7867401 -e NEEDLE_SEEDS=7867401,7867601,7867801 -e NEEDLE_OUTPUT=/src --entrypoint python needle-pilot05:local /src/paired.py
```

## Sole formal allocation

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<frozen-source>,target=/src,readonly" --mount type=volume,source=unjuno-needle-role-c-support64-replication-4884-v1,target=/out --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEED=7867401 -e NEEDLE_SEEDS=7867401,7867601,7867801 -e NEEDLE_OUTPUT=/out --entrypoint python needle-pilot05:local /src/paired.py
```

Independent raw-only audit uses a separate network-disabled, read-only container mounting the same volume read-only: `/src/audit.py /out`. No retry or seed substitution.

