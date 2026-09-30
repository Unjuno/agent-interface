# Host construction smoke — not the formal container allocation

Run once on 2026-09-30 from the frozen candidate before the pending
OrbStack allocation. This verifies JSON serialization and raw-only audit wiring;
it is explicitly excluded from the formal result and is not a substitute for
the requested container execution.

- Runner command: `python3 -B run.py results/construction-host-01/raw.json`
- Exact stdout: `{"cells": 27, "output": "results/construction-host-01/raw.json", "scenarios": 9, "status": "PASS_FINITE_T0_EXECUTED"}`
- Auditor command: `python3 -B audit.py results/construction-host-01/raw.json`
- Exact auditor stdout: `{"cell_count": 27, "errors": [], "status": "PASS_READONLY"}`
- Raw SHA-256: `75b135aac6d67168ac31c9d727fc5a7052bd88fc75b8bf7221a98f85f63b6461`

Across nine cells per policy, all policies recorded 18/18 target completions and
zero unsafe admissions. Collision retries were no-coordination 8, local markers
5, central claims 0. Coordination event counts were 0, 12, and 36 respectively
(local marker publish/observe events versus central request/grant messages are
not equivalent units). In the primary visible-contention cell, local markers
reduced retries 1→0 versus no coordination and recorded 2 events versus 4
central claim messages. In the no-contention control, local markers added
coordination events without reducing retries.

These are deterministic hand-specified logical-tick model outputs, not measured
wall-clock behavior or real agents. The raw-only audit and construction tests
validate this host smoke only. Formal allocation `stigmergic-coordination-5346-t0-20260930-01`
remains unconsumed: no container runner or container auditor has been invoked.
