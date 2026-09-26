# Construction 02 — STOP

**Classification:** `STOP_FAKE_EXECUTABLE_TMPFS_NOEXEC`.

The path initialization correction passed, and the construction probe compiled the mounted broker, test runner and auditor. It then wrote the deterministic fake to `/tmp` and applied mode 0755, but `execve` failed with `PermissionError: [Errno 13] Permission denied`. The bounded Docker tmpfs was mounted without its `exec` option, so the filesystem correctly refused to execute the fake.

No broker invocation or formal case ran. Docker container exit was 1. The failed construction remains separate from construction-01. The preregistration now explicitly grants execute permission only on the bounded `/tmp` tmpfs that contains the generated fake; rootfs/source remain read-only and the container remains network-isolated.
