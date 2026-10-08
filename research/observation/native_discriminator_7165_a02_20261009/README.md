# #7165 A02 — context invalidation and fresh fallback

This additive analytical experiment tests one unresolved boundary named by
Issue #7165 after A01: whether a remembered cue requirement is invalidated when
its source generation or cue provenance is not current, and whether the path
then returns to full fresh revalidation. A01's native failure remains intact.

The finite fixture contains two cues (`title`, `parent`), two identities,
missing observations, stale/wrong-source read statuses, incomplete requirements,
and both matching and stale context generations. Its decision oracle binds only
when both current cues agree; otherwise it returns `UNKNOWN`. The remembered
requirement carries no identity value or action authority. Candidate output is
compared to always-fresh full revalidation, with an independent raw-only audit
and corruption controls.

This is a deterministic finite-contract experiment, so no container, X server,
model, application, or timing run is required by its claim. It does not measure
native context invalidation, observation bytes, model-boundary cost, or user-task
benefit. Cue provenance labels are assumed truthful in the model; forged labels
and asynchronous changes within an unchanged generation remain outside scope.
Even a method-scoped PASS will not establish a memory-specific work reduction.

See `PLAN.md` for H/T/D/C/U and allocation identity. `FREEZE.json`, the
candidate raw result, the independent audit, and the final disposition are
written after the single frozen run.
