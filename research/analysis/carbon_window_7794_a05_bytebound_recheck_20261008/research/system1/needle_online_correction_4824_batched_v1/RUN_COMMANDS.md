# Reproduction commands — construction only

Pinned image: `needle-pilot05:local`, ID `sha256:6ab7a93188ddf4232a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU. Source is mounted read-only, root is read-only, network is disabled, and the dedicated construction volume is the only writable persistent output.

Run once:

```powershell
$src = (Resolve-Path .).Path
docker volume create needle-online-correction-4824-batched-construction-v1
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 --pids-limit=64 --security-opt=no-new-privileges -e PYTHONPYCACHEPREFIX=/tmp/pycache --mount "type=bind,source=$src,target=/src,readonly" --mount type=volume,source=needle-online-correction-4824-batched-construction-v1,target=/out --entrypoint python3 needle-pilot05:local /src/runner.py
```

Independent audit, in a separate container with raw output mounted read-only:

```powershell
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 --pids-limit=64 --security-opt=no-new-privileges -e PYTHONPYCACHEPREFIX=/tmp/pycache --mount "type=bind,source=$src,target=/src,readonly" --mount type=volume,source=needle-online-correction-4824-batched-construction-v1,target=/out,readonly --entrypoint python3 needle-pilot05:local /src/audit.py /out/construction/raw.json
```

The recorded outcome is construction-only and must not be promoted to the Issue's formal decision. No formal trainer/auditor invocation was used.

