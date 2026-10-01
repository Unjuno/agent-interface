# Exact local commands

Image ID before formal: `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (`linux/amd64`). Output volume was created new and verified empty before the run.

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-c-support64-diagnostic-4848-v1,target=/src,readonly" --mount type=volume,source=unjuno-needle-role-c-support64-diagnostic-4848-v1,target=/out --tmpfs /tmp:rw,noexec,nosuid,size=64m -e NEEDLE_SEED=7866201 -e NEEDLE_OUTPUT=/out --entrypoint python needle-pilot05:local /src/paired.py
```

The only formal invocation exited before model construction. It is not repeated.

```powershell
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --mount type=volume,source=unjuno-needle-role-c-support64-diagnostic-4848-v1,target=/raw,readonly --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-c-support64-diagnostic-4848-v1,target=/src,readonly" --entrypoint python needle-pilot05:local /src/audit_stop.py /raw
```

Auditor output: `STOP_NO_RAW_OUTPUT`, `entries=[]`, `optimizer_updates=0`, `seed_reusable=false`.

