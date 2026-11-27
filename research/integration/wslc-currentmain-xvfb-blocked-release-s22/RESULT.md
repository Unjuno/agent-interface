# S22 WSLc current-main private-Xvfb blocked-release replicate

S22 passed the unmodified current-main standard-caller Xvfb test on WSLc 3.0.3 at a 3,860 ms private X-server pause and a 4,000 ms transaction deadline. The process/input release readback completed 3,921.388 ms after cancellation admission, leaving 78.612 ms before the deadline. A separate parent X client independently read all keys up at 4,219.074 ms after cancellation start; the delayed-request horizon was 8,502.261 ms with no delayed `b` keypress.

The old and fresh synthetic task oracles both passed, including exact non-idempotent effect counts. The public runtime cancellation result remains `UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`. The independent supervisor receipt and synthetic application effects do not promote that public result. This is a private synthetic Xvfb experiment; it makes no physical desktop, real application, MAP01, efficiency, or reliability claim.

The pinned Ubuntu image ran with no network, 2 CPUs, 2048 MB requested memory, GPU disabled, and read-only repo/dependency/stage/XKB/runner mounts. The result directory was writable. The WSLc API path does not expose the Docker-only pids limit and executable `/tmp` tmpfs settings used by R46; those are recorded as condition differences. Exact container, image, and session cleanup succeeded.

S21 is preserved separately as a zero-input runner setup failure caused by CRLF in `container-init.sh`; no Xvfb or caller test started. S21 was not retried. S22 used a fresh attempt ID, WSLc session, storage directory, and output directory.

See [PREREGISTRATION.json](PREREGISTRATION.json), [AUDIT.json](AUDIT.json), and the raw files in `output/`. Re-run the local evidence audit with `python audit_s22.py` on a host with the original read-only R09/R16/R34 trees available.
