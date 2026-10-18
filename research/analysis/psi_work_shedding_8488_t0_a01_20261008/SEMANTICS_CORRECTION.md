# Post-run deadline-semantics correction

The original report's `NO_RESIDUAL` interpretation is superseded by this qualification. No frozen source, input, candidate output, or auditor output was changed, and neither formal CLI was rerun.

`PROTOCOL.md` defines `deadline` as an **exclusive completion bound**. A task is on time only when it has completed strictly before that bound. In the raw output, however, the candidate records a deadline miss only after processing the deadline-indexed tick and only if the task is still incomplete (`candidate.py`, lines 91–93). Because completion is recorded as `tick + 1`, a task completed at exactly its deadline is omitted from the candidate's miss set. The independent auditor reconstructs the candidate's same rule, so its exact 32/32 replay did not detect the protocol/implementation mismatch.

A post-run, read-only reconstruction over the frozen input and immutable raw counts an uncompleted job or any job with `completed_at >= deadline` as late. It finds disagreements in 8 of 32 rows. On the primary trace the corrected miss sets are: fixed concurrency 4; queue/deadline 3; free-memory 4; PSI-memory 1. Thus the apparent strict PSI improvement remains descriptive, but the preregistered zero-primary-miss gate fails. The formal result is **`HOLD_DEADLINE_SEMANTICS_MISMATCH`**, not `NO_RESIDUAL` and not a PASS.

Exact input/raw identities, all eight differing rows, corrected primary gates, and the no-rerun declaration are in [SEMANTICS_CORRECTION.json](SEMANTICS_CORRECTION.json). Any corrected candidate/auditor study needs a separately versioned successor allocation, corrected tick contract, and fresh collision/freeze checks.
