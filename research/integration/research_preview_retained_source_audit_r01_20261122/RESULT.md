# Research Preview retained source audit R01

Status: PASS_FROZEN_SOURCE_AUDIT; offline integration check only.

- Base main: `128c33f22a042b83a51351debdc32ef3ae5bfa4b`; candidate implementation commit: `2552fe76eaffe8abd85328fe115b2f1f3df91d63`.
- Frozen experiment source commit: `54910c6f9f0594c609f1f3c6895a918caa64130f`; archived source files verified: 29; archive mismatches: 0.
- Current source content drift, compared with the archive after line-ending normalization: 7 of 29 files. This matches Git-blob comparison; checkout conversion is not counted as content drift.
- Retained outcome remains `RETAIN`, six tasks per arm, break-even task 2.
- Local tests: retained-audit tests 5/5 normal and `-O`; preview bundle builder 5/5 normal and `-O`; actual retained audit exit 0.
- No live mode, model call, GUI, allocation, task action, or dependency installation occurred. Raw commands, stdout/stderr, exit codes and conditions are retained in this directory with SHA-256 custody.
