# r415 result

PASS, one WSLc trial. Unguarded control connected to both private X servers. After installing server A's pidfd-backed process-wide connector, target-query and read-only observation constructors each connected to A from a separate thread and rejected B with `RuntimeError: display peer mismatch`. Both servers reported retired and the guard closed. Raw stdout/stderr and exit code are in `run.txt` and `exit.txt`; frozen conditions and runner are retained. Host warned that swap limits are unavailable.

This uses constructors in a disposable process, not an MCP owner session; it does not test same-number server replacement or independently capture socket peer credentials. B was independently confirmed reachable before installing the guard, and its rejection occurred with the connector's peer-mismatch error before X authentication. No key input or model calls were made. It does not establish full connection coverage or recovery.
