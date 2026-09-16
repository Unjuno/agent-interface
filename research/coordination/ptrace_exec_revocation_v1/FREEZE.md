# Source-first freeze — kernel-observed exec revocation v1

Task `COORD-PTRACE-EXEC-REVOCATION-20260917-027`, Issue #636.
Publication BASE `69e5665cb30f6c49200395343450b3f829e28804`.
Formal allocation `ptrace-exec-revocation-20260917-a1`.

The helper sends only setup READY before GO so the same-UID supervisor can attach. After GO it sends no lifecycle report and execs the task. The single intervention is whether `PTRACE_O_TRACEEXEC` is enabled and the resulting kernel exec-stop is used to revoke the grantor endpoint before `PTRACE_CONT`.

Formal schedule is exactly the 12 `m*` cases in `plan.json`, executed as six independently invoked two-case chunks from the start. No measured-ID rerun, replacement or extension. Excluded construction uses only `c*` IDs. The pre-freeze ptrace construction supervision fix for post-exec SIGPIPE is retained in Issue #636 and no formal case existed before this freeze.
