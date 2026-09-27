# Issue #4881 execution record

Image: `needle-pilot05:local`, ID `sha256:6ab7a93188ddf4232a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (Linux/amd64 CPU). Source mounted read-only, network disabled, root read-only, 1 CPU, 2 GiB, 64 PIDs.

## Construction (zero optimizer updates)

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<frozen-source>,target=/src,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEEDS=7866801,7867001,7867201 --entrypoint python needle-pilot05:local /src/construction_test.py
```

Result: `CONSTRUCTION_PASS seeds=3 prefix_exact=True streams_disjoint=True byte_sentinel=True corruption_rejected=True optimizer_updates=0`.

## Sole formal invocation — STOP before training

The dedicated volume was created empty, then the wrapper was invoked once:

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=<frozen-source>,target=/src,readonly" --mount type=volume,source=unjuno-needle-role-c-support64-replication-4853-v1,target=/out --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEEDS=7866801,7867001,7867201 -e NEEDLE_OUTPUT=/out --entrypoint python needle-pilot05:local /src/paired.py
```

Observed `KeyError: 'NEEDLE_SEED'` from pinned upstream module import at line 6. No optimizer step occurred; no result files were written. Read-only inspection confirmed the volume has no files. The raw-only audit was then invoked once against that empty volume and correctly returned `FileNotFoundError: /out/summary.json`; it did not emit PASS. This allocation is consumed, no retry.

Local frozen-source SHA-256: paired.py `FFAD50937D76FD218B7379D11E6CE38D0E5CFB7EDC78749D6C90C7F68FCA3307`; audit.py `27B49248CE859482A0534D9F9B2E53439DE72936798F4F4C4F5550B63903ECF9`; construction_test.py `467A6088BBE9185B4888FAD2A3AB92DFCC139D60F65C71C4D5C56C5AB255379C`; prefix_contract.py `5064F6DB181F9B97A9EE9B0F59D8D275291038BD26A3FCD7451424500ACD652F`; upstream_runner.py `A0E99B991A8A3AB9B2F4B6F4F22F7C705989447CE64A14738026FCD763B55ABB`.

