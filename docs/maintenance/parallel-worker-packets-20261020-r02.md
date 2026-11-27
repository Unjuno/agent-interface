# Parallel worker packets r02 — 2026-10-20

Baseline: `main` at `ee40a4467f3dd3cba4ba376d188cd3597a15a35e`, after PR
#9258. The complete paginated [r116 membership recheck](repository-inventory-recheck-20261020-r116.md)
matches r114 exactly: 1,672 open Issues and 468 open PRs. Reuse r114 row-level
metadata; r116 is membership only and does not refresh owners, PR heads/checks,
semantic disposition, or evidence custody. The [r05 worktree census](git-worktree-census-20261020-r05.md)
records 37 registered roots, 10 dirty, none locked or prunable. It is not a
deletion list. Use the [cleanup plan](../REPOSITORY_CLEANUP_PLAN.md) as the
canonical policy and this file as a dated dispatch surface.

The earlier [r01 packet](parallel-worker-packets-20261020-r01.md) is historical.
Several exact PRs in it have since closed or merged. Current-state spot checks
confirm #8832, #8840, #8843, and #8848 are closed; their retained results and
successors are recorded in the cleanup plan and idea-family records. Do not
assign those closed PRs as open work.

## Completed independent audits to integrate

These audits are reports, not assignments and not state-change authority:

| Item | Exact GitHub state | Verified finding | Integrator disposition / next finite action |
|---|---|---|---|
| [PR #8832](https://github.com/Unjuno/agent-interface/pull/8832) | Closed; head `631b9dfc16f5f682eab72ad1a88ed6fc9fce25c6`, base `6206b06fa93958911f4a9231b6152f7ff1470eb4`. | Its scoped #8574 result was retained under merged successor #9217. The test audit depended on an uncommitted absolute-path golden fixture and was not clean-checkout reproducible. | Keep the consumed result and test-harness defect distinct. Any future harness repair must be a new current-main change; do not rerun the consumed allocation. |
| [PR #8836](https://github.com/Unjuno/agent-interface/pull/8836) | Open, non-draft; head `afab8e406164e2e69de6ec25ba1724fa22f01d4e`, base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. | Audit retains `FAIL_COST_GATE_SCOPED`. | Before merging, recheck exact diff and evidence. A cost-accounting repair must use a current-main successor and must not rerun its consumed allocation. |
| [PR #8841](https://github.com/Unjuno/agent-interface/pull/8841) | Open/draft; head `04e7ddaa583fb3b120e9f3d00f3249c79c304f04`, base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. | Construction-boundary tests are retained, but the #59 live threat exposure is unverified. | Preserve as construction evidence; compare its source/tests with current main and decide transfer or hold. It is not a live-control completion. |
| [PR #8844](https://github.com/Unjuno/agent-interface/pull/8844) | Open/draft; head `b9f4221cdbee93e4186f19ab659f51dca0bc5cea`, base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. | A04 remains `HOLD_UNCERTAIN`, with unique evidence to preserve. | Verify the exact raw/audit package and current-main successor status before any disposition. Do not rerun the candidate or auditor. |
| [PR #8845](https://github.com/Unjuno/agent-interface/pull/8845) | Open/draft; head `a8abd5afaccd35927752d857edfab679f96145c9`, base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. | Its shared WSLc lane dependency is unresolved. | Keep on hold until the exact shared-lane owner/release is verified; do not start WSLc/Docker work. |

The PR heads above were re-read from GitHub on 2026-10-20. Their base SHAs,
authors, checks, review threads, and ownership must be refreshed before a PR
state change. In particular, an open state is not an assignment and a closed
state is not permission to remove its branch or worktree.

## Disjoint read-only family packets

Each packet may be reviewed independently by a worker using its own private
output file. These are finite review scopes, not active ownership assignments
or shared-resource grants. Before beginning, record the live Issue/PR state,
worker/session identity, registered worktree path, branch, HEAD, complete Git
status, and exact source/output scope. If an active owner or conflicting writer
is found, report the conflict and leave the shared record untouched.

| Packet | Exact scope | Finite output | Hard boundary |
|---|---|---|---|
| WSLc execution economics | Issues #6389, #6693, #8518 and directly linked PRs/evidence | For each distinct hypothesis, give current owner/release evidence, matched-arm availability, retained first result, and one condition to resume. | No WSLc or Docker invocation; do not infer release from process counts. |
| WSLc readiness and eligibility | Issues #7924, #7970, #8150 and directly linked records | Separate runtime ownership/release from threat-profile method review; report exact current gate and one finite unlock condition per Issue. | No runtime invocation and no sandbox certification. |
| Consumed auditor-failure custody | Issues #8446 and #8455, their source packets and closed successors | Confirm the distinct failure modes, preserved raw/manifests, current canonical links, and one reopen trigger for each. | No rerun, reconstructed allocation, or pooling of outcomes. |
| Idea-only candidate discovery | One worker-selected, disjoint family from the current index gap queue | Identify at most one coherent family; link each Issue to its own hypothesis, first outcome/raw, limits, dependency, next decision, and source backlink. | Do not close on a title or count. Verify each Issue live and preserve distinct siblings. |

The first three packets preserve earlier r01 scope but require fresh live
verification. The fourth packet is intentionally narrow: use the historical
r51/r52 coverage reports only to find candidates, then verify each exact Issue,
family, PR, and owner against current sources. It is not a license to classify
all 1,672 Issues by number or to split one family across multiple writers.

## Integration and closure protocol

1. Workers save additive findings to separate private paths and report exact
   sources, outcome/limits, conflicts, and a next decision. They do not edit
   `WORKER_WORK_MAP.md`, the shared idea indexes, or this dispatch file.
2. One integrator reconciles each report against live GitHub state and current
   main, then updates the canonical family record and worker map once per batch.
3. Keep Issues open when a distinct question, live experiment, dependency,
   evidence gap, or explicit hold remains. Close an Issue only after that
   Issue's own question is complete or faithfully transferred, its canonical
   idea/evidence record is complete, and source, successor, and return links
   are verified on both sides. Cataloguing alone is not scientific completion.
4. Reconcile PRs separately by exact head/base, full diff, local validation,
   dependencies, and retained evidence. Merge only verified useful work under
   the repository's actual current protections; close as superseded only after
   successor content and links are verified.
5. Do not move, archive, or delete branches, worktrees, ignored files, or raw
   data from this dispatch. Physical cleanup requires an item-specific owner,
   process/session, dependency, unique-evidence, and recovery-path check.

This packet set is meant to let independent workers review disjoint families
while serializing edits to shared indexes. Completion means every reviewed
item has a traceable disposition and safe next action, not zero Issues, zero
PRs, or zero worktrees.
