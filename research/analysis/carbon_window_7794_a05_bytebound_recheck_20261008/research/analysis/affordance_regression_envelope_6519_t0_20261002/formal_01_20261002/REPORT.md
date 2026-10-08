# Formal allocation 01 — STOP

The single construction command attempt returned exit 1 before any test output. The launch shell was rooted at the workspace rather than this repository worktree, so its relative `Resolve-Path` did not find the package and the source/output mount variables were null. WSLc has no retained container named `affordance-6519-construction-01`; no candidate or auditor ran.

The construction allocation is conservatively treated as consumed. No retry, source repair, or scientific interpretation is made under this allocation. This is an execution-path failure, not evidence for or against the annotation-regression method. The exact attempted command shape and observed shell diagnostics are summarized in `construction/STOP.json`. A separate allocation would require absolute-path validation before freeze and distinct outputs.
