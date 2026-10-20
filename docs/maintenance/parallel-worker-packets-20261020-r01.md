# Parallel worker packets r01 — 2026-10-20

Baseline: refreshed `main` at `282a05b02d8d48053c88bcdb08ace54694068a6`; live membership is recorded in [inventory r100](repository-inventory-20261020-r100.md). Compared with r98, #8574, #8832, and #8843 are closed with scoped outcomes or merged evidence successors recorded in the cleanup plan; their closure does not resolve the broader research families. These packets convert cleanup into bounded, independent reviews while retaining source Issues, failed outcomes, and evidence limits. They are not assignments, shared-resource grants, or authorization to run WSLc/Docker experiments. Workers should return private notes/artifacts to one integrator; only the integrator updates shared indexes and this map.

## Worker contract

For each task, record the exact source Issue/PR, current URL/state, head/base SHA where applicable, absolute registered worktree path, `git rev-parse --show-toplevel`, HEAD/branch, complete porcelain status including untracked files, and exclusive task scope. Use a distinct registered worktree and branch for each writer. Read-only audits may share a checkout. Raw experiment evidence is immutable. Do not reset, delete, prune, move, or reuse a directory/branch whose owner or evidence custody is unknown. Do not close an Issue or PR to reduce counts. Before a state change, refresh live owner, dependencies, exact head/base, checks, comments, and evidence custody.

The 2026-10-20 local custody audit found 29 registered worktrees, 8 dirty; the canonical checkout is itself dirty. It found 133 local branches and 212 immediate `work` directories, which include experiment/output folders. These observations are not proof that any unregistered-looking folder or unoccupied branch is disposable. Audit packet results and verify worktree status at assignment time.

## Issue-family review packets

| Packet | Exact Issues | Allowed work and finite exit | Boundaries / dependencies |
|---|---|---|---|
| WSLc execution economics | [#6389](https://github.com/Unjuno/agent-interface/issues/6389), [#6693](https://github.com/Unjuno/agent-interface/issues/6693), [#8518](https://github.com/Unjuno/agent-interface/issues/8518) | Read-only source/evidence and live-comment lineage audit. Report whether an owner/release exists for the shared lane and whether a matched Docker arm exists; otherwise record `HOLD` with one concrete prerequisite per issue. | Distinct questions: route eligibility/portability, same-host Docker-vs-WSLc cost, API-session-vs-CLI amortization. No WSLc/Docker invocation; #6693/#8518 have shared-lane and environment-parity dependencies. |
| WSLc readiness and eligibility | [#7924](https://github.com/Unjuno/agent-interface/issues/7924), [#7970](https://github.com/Unjuno/agent-interface/issues/7970), [#8150](https://github.com/Unjuno/agent-interface/issues/8150) | Refresh owner/release and clean-current-main evidence for #7924/#7970; separately reconcile #8150's blind review records and determine whether a method-only follow-up remains. Exit with item-by-item `HOLD`/eligible findings and source links. | No WSLc runtime call or security certification. #7924/#7970 require explicit lane ownership/release; #8150's prior blind split and HOLD remain intact. |
| Consumed auditor failure custody | [#8446](https://github.com/Unjuno/agent-interface/issues/8446), [#8455](https://github.com/Unjuno/agent-interface/issues/8455) | Read-only comparison of source records, closed successor PRs, exact saved evidence and manifests. Identify whether a distinct evidence/catalog gap survives; preserve the consumed failures and report one reopen trigger. | Do not rerun/recreate consumed allocations. Keep A03 `KeyError: absence_verified` distinct from A04 `KeyError: cid` and the separate colliding-r3 HOLD. |

## PR review packets

| Packet | Current PR | Next finite action | Disposition boundary |
|---|---|---|---|
| Win32 release-state repair | [#9006](https://github.com/Unjuno/agent-interface/pull/9006), head `655a5bcdf6026650044e0157343d4e0de268a548`, base recorded `1ece47014d05db898bf73afcd722a14524462e15` | Resolve the reported Win32 release-state contract and native-mcp failure against current main; refresh and run affected checks on the exact new head. | Draft, `UNSTABLE`; not merge-ready. Keep synthetic scope. |
| Conflict repair / current-main validation | [#8756](https://github.com/Unjuno/agent-interface/pull/8756), head `e12eb7e9b8a5414863e22e69545108933f15d6b8`, base `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36` | Resolve the current conflict, inspect the refreshed exact diff, rerun focused tests, and record a current-main disposition. | Draft, `DIRTY`, 26 files; prior checks apply only to stale head. Preserve synthetic-method limit. |
| Evidence/candidate status review | [#8861](https://github.com/Unjuno/agent-interface/pull/8861), head `cc3e6b1c83780e1419186b574a4dc4119b4e7c24`, base `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | Resolve conflict and establish whether a formal candidate/full-auditor run exists; if not, leave parked with the missing evidence explicit. | Draft, `DIRTY`, 5 files; A04 remains `HOLD_UNCERTAIN`. Do not promote construction-only evidence. |

The three PRs are separate, independently scoped review packets. None was judged merge-ready in the 2026-10-20 live audit. A green check on a stale head is not current-main verification. Do not assign two writers to the same PR or modify shared indexes concurrently.

## Integrator follow-up

After each packet returns, refresh the exact live record and compare the worker's source refs with current main. Put findings into a private packet first; reconcile the selected family index and `WORKER_WORK_MAP.md` in one serialized integration pass. Keep actionable/blocked Issues open. Catalog an idea only when its hypothesis, all material outcomes, raw evidence, scope limits, dependencies, next decision, and reopen condition are preserved. A smaller Issue/PR count is not a completion criterion.
