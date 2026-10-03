# Report — #5368 WSLc portability replay

**`PASS_PORTABILITY_SCOPED`** — the frozen candidate and independent raw-only auditor each ran once in WSLc and exited 0. Candidate/baseline outputs and audit JSON are byte-identical to the preserved Windows-host result; the audit reconstructed 9/9 rows, found 0 unsafe admissions, and detected 4/4 mutations.

This confirms portability for the exact finite synthetic workload and pinned Python image only. WSLc emitted a cgroup/swap-limit warning, retained in `RUN.json`; no timing, RSS, memory-pressure, hard-cap, Docker comparison, or broader migration benefit is claimed. Full protocol and H/T/D/C/U scope are in `README.md`, `FREEZE.json`, `RUN.json`, and `RESULT.md`.
