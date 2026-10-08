# Audit attempt 02 — launcher STOP

Allocation: `w2-draft2020-12-meta-audit-20260928-02`.

**Disposition: `STOP_WINDOWS_TO_POSIX_ARGUMENT_QUOTING`.** The PowerShell-constructed `docker run ... sh -c` argument was mangled before the container could run its installation/audit sequence; `/bin/sh` reported `Syntax error: Unterminated quoted string`. The results-v2 directory is empty. Neither meta_audit.py nor independent_audit.py began, and no schema conclusion exists. Do not rerun allocation 02.

The next successor must invoke a checked-in/frozen Python launcher as the Docker entrypoint directly, avoiding a nested shell command string. Keep this failure separate from allocation 01's native-extension tmpfs STOP and all W2 results.
