# Static preflight STOP01 — read-only importroot

Separate preformal preflight container; no public MCP initialization, display, app, or GUI input occurred. Command attempted `mkdir -p /opt/importroot` in a `--read-only` container without a writable mount at that path and exited 1 with:

```text
mkdir: cannot create directory ‘/opt/importroot’: Read-only file system
```

The runner, auditor, and preflight files were mounted read-only and unchanged. This is a container mount-layout setup STOP, not a scientific result and not a formal allocation. A distinct static-preflight container will place only `/opt/importroot` on tmpfs; no experiment outcome will be pooled or rewritten.
