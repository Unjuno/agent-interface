# A03 retained execution STOP

Allocation `CONFUSION-ADAPTIVE-PRACTICE-8084-A03-20261005-01` is stopped at the audit-input handoff. The candidate was invoked exactly once in the frozen read-only WSLc mount and exited 0; stdout is retained at `results/candidate.stdout.json` (449,004 bytes), stderr at `results/candidate.stderr.txt`. Fixture generation exited 0 and emitted 6,000 rows; its stdout/stderr are retained.

The auditor was invoked once and exited 1 because its required `candidate.raw.json` was not present in the auditor-only directory. The host-side `Copy-Item` used `..\results\candidate.stdout.json` while running from the package root, resolving to the wrong directory; that copy failed before writing any audit input. Auditor stdout is empty and stderr preserves the `FileNotFoundError`. The WSLc kernel/cgroup warning was also retained in the log. The candidate output is not interpreted as a result because no independent audit completed.

**Disposition:** `STOP_AUDIT_INPUT_HANDOFF_PATH_ERROR`; accepted row audit count 0/6,000; no scientific support/no-support conclusion. The consumed A03 candidate and failed A03 audit are not rerun or reused for an accepted result. Any follow-up uses a separately named fresh allocation and fresh deterministic seeds, and the copy path is validated before execution.
