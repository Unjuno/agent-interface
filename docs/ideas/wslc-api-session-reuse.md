# WSL Container API session reuse — #8518

- **Source:** Open, unassigned [Issue #8518](https://github.com/Unjuno/agent-interface/issues/8518), last updated 2026-10-08, with no comments; it is a successor to [#6693](https://github.com/Unjuno/agent-interface/issues/6693).
- **Status:** Proposed and unverified. The live Issue says no candidate or runtime operation is authorized and records no run. The latest [#7970 gate note](https://github.com/Unjuno/agent-interface/issues/7970#issuecomment-6118372633) and [#6389 HOLD](https://github.com/Unjuno/agent-interface/issues/6389#issuecomment-6062418714) leave WSLc/Docker work stopped pending owner reconciliation and a clean attributable current-main checkout.

## Distinct question

On one pinned low-risk CPU workflow, compare 12 fresh WSLc CLI `run --rm` invocations with 12 paired iterations that reuse one WSL Container API `Session` but create and explicitly remove a fresh container for every iteration. This isolates session setup reuse; it does not reuse a writable task container or assume that a WSL session behaves like a database connection pool.

The proposed thresholds are either at least 10% lower median end-to-end time with no more than 5% host-visible peak-memory regression, or at least 10% lower host-visible peak working set with no more than 5% time regression. The full decision rule additionally requires correctness/raw equivalence, audit and cleanup success in every block, and paired randomization testing with Holm correction across the two primary endpoints. Requested cgroup limits and client RSS alone do not establish host-memory improvement.

## Required gates and preservation

The Issue requires a fresh owner/collision check, exact current-main source, explicit exclusive WSLc-lane release, pinned source/image/architecture/runtime versions, balanced arm order, and a usable fixed image before formal work. It prohibits Docker startup, induced memory pressure, overlapping workloads, and persistent writable task containers. Every iteration must retain raw output, audit, process/container identity, lifecycle receipt, teardown evidence, and separately attributed Windows process-tree, WSL VM, and guest-memory measurements. First formal failure is terminal for its allocation.

Current proposal status is therefore `0/0` candidate/auditor, with no performance, memory, cleanup, isolation, or parity result. This API-session lifetime question differs from #6693's same-host Docker-versus-WSLc cost comparison and #7430's native WSL versus WSLc memory comparison. Neither Microsoft API availability nor the #6352 portability result supplies an answer.

**Next finite decision:** Read-only verify explicit exclusive-lane owner/release, an attributable clean current-main checkout, and the pinned fixed image/source needed by both arms. If any gate is absent or unknown, retain HOLD and perform no WSLc/Docker operation. Only after all gates are clear, consider a separately frozen API-session-versus-CLI allocation with fresh containers; the #6693 Docker comparison and its outcome do not answer this estimand.
