# Native macOS read cancellation boundary

Parent #6501; finite adapter I/O recovery requirement #57. This source-first archive fixes eight owned native macOS rows, one producer and one primary raw reader with zero retries. Formal execution has not occurred at this source commit. See source/PLAN.md and source/PROTOCOL.json for H/T/D/C/U and limits. Results will be added as immutable first outputs; historical zero counts refer only to this pre-execution snapshot. Python snapshots are inert .py.txt files and are never imported or discovered by repository test/workflow entry points.

Distinct from Linux #6915 completion, Windows #6897 gated-callable, Mac #6927 co-ready priority and Linux #6942 FD-reuse schedules. No kernel syscall proof, arbitrary I/O preemption, physical input release, task benefit or performance claim.

Current retained first output: [REPORT.md](REPORT.md), eight native rows/114 events, producer/primary auditor1/1, retries0. The preceding zero-count text is the immutable preexecution source snapshot. Publication is a review-pending inert archive.
