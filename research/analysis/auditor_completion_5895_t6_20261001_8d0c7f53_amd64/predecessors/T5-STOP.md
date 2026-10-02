# T5 terminal STOP before candidate

Time: 2026-10-01 12:12:05 UTC.
Allocation: `AUDIT-COMPLETION-5895-T5-ORB-20261001-01-8d0c7f53`.
Disposition: `STOP_PREREG_PLATFORM_SCOPE_MISMATCH / NOT_EVALUATED`.

At the fresh start gate, canonical Issue #5895 explicitly required a pinned Linux/amd64 Python image in its **C** boundary. T5 had preregistered Linux/arm64 in `PREREG.md` and `FREEZE.json`. The execution platform therefore did not match the idea being tested. I did not alter the Issue's scope, edit the registered T5 preregistration, pull or inspect an image, call Docker, or launch a candidate.

Counts: Docker run/container 0; candidate 0; target cases 0/8; independent auditor 0; retries 0. No scientific result exists. The owner-bound T5 OrbStack window 12:10–12:30 UTC was released immediately.

GitHub records: [Issue #5895 STOP comment #5931146854](https://github.com/Unjuno/agent-interface/issues/5895#issuecomment-5931146854), [coordination release #5931147504](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5931147504). T5 remains a terminal predecessor and must not be reused. Any continuation needs a distinct allocation/branch/path and a Linux/amd64 preregistration. The pinned digest/platform must be confirmed locally before candidate execution; unavailable amd64 is a pre-candidate STOP, not grounds to switch back to arm64.
