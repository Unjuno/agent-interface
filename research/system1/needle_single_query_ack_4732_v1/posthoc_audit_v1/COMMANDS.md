# Reproduction

Pinned image: `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (`linux/amd64`, Python 3.12.14, PyTorch 2.5.1+cpu). Docker client/server: 29.8.0/29.8.0.

From the experiment directory, first run the schema/gate regression tests:

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --mount "type=bind,source=$((Get-Location).Path),target=/src,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=128m --entrypoint /usr/local/bin/python needle-pilot05:local -B /src/posthoc_audit_v1/test_posthoc_audit.py
```

Then run the post-hoc replay in a separate container. Mount the experiment source, frozen baseline and formal raw read-only, the existing named formal volume read-only, and a new output directory read-write:

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --mount "type=bind,source=$((Get-Location).Path),target=/src,readonly" --mount "type=bind,source=$((Resolve-Path baseline).Path),target=/baseline,readonly" --mount "type=bind,source=$((Resolve-Path formal\training).Path),target=/raw,readonly" --mount "type=bind,source=$((Resolve-Path formal\posthoc-audit-v1).Path),target=/out" --mount type=volume,source=unjuno-needle-single-query-ack-4732-formal-v1,target=/volume,readonly --tmpfs /tmp:rw,noexec,nosuid,size=128m --entrypoint /usr/local/bin/python needle-pilot05:local -B /src/posthoc_audit_v1/posthoc_audit.py --raw /raw --volume /volume --frozen-audit /src/audit.py --baseline /baseline/study.py --out /out
```

The first container ran the two unittest cases; stdout is retained in `test.stdout.txt`. The replay's final result is in `POSTHOC_AUDIT.json`; stdout is retained in `audit.stdout.txt`. PyTorch emitted a NumPy-not-installed warning because this intentionally minimal image has no NumPy; validation completed successfully.
