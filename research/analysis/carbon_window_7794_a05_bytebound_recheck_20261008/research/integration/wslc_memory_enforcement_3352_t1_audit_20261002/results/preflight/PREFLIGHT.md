# Preflight observations

The original exact multi-mount preflight failed once with WSL `E_FAIL`; no audit code ran. After read-only diagnostics, a no-mount pinned-image smoke returned `WSLC_SMOKE_READY`, exit 0. A separately authorized exact mount-only preflight then returned:

```text
READY
preflight_exit=0
```

The successful preflight confirmed the original local packet, frozen auditor digest, and writable output directory were available at their distinct mounts. It did not execute the auditor or read/interpret the memory-probe outcome. See `PRE_FORMAL.md` for the full sequence.
