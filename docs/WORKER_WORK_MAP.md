# Worker work map

2026-10-19 update. Cursor-paginated GitHub REST reads returned 1,676 open Issues
and 515 open PRs. Against [r8](maintenance/repository-inventory-20261018-r8.md),
Issue ID membership is unchanged and PR #9039 is the only addition. The captured
main SHA is `4e36e47a690621a658515b5107cce020dfe6df82`; see [r9 inventory](maintenance/repository-inventory-20261019-r9.md)
for timestamp, CSV checksums and exact metadata. This is not semantic review or
proof of current ownership. R8 and earlier snapshots are historical. Begin with
[current goal](CURRENT_GOAL.md), choose one finite item
below, and verify its current Issue, source and ownership. This map is navigation;
it adds no assignment, resource grant, reviewer quota or all-workers waiting gate.
The full outcome and safe closure criteria are in the [repository consolidation
execution plan](REPOSITORY_CONSOLIDATION.md#実行計画-r26--アイデアを保全した全体収束). The local, read-only
workspace artifact snapshot is [separate from repository contents](maintenance/workspace-custody-census-20261019.md);
unknown custody means preserve and investigate, not delete.

## Choose work

| Scope | Existing question / evidence | Next finite deliverable | Collision boundary |
|---|---|---|---|
| Repository and ideas | [Consolidation plan](REPOSITORY_CONSOLIDATION.md), [r76 historical status](maintenance/consolidation-status-20261016.md), [idea index](ideas/README.md), [r9 current metadata inventory](maintenance/repository-inventory-20261019-r9.md) | Choose a research family by its question and evidence, then read the current Issue, necessary comments, related open/closed PRs and exact current heads. Add a concise hypothesis/evidence/residual/next-test entry; mark missing evidence `unverified`. Update the family note and Issue disposition only after checking original scope and retained evidence. | Declare disjoint Issue/PR numbers, code area and output file before parallel work. Separate families may proceed independently; write family-specific notes separately and serialize edits to shared indexes. Do not use age, draft state or empty assignee fields as closure evidence. |
| Input authority and release | [#17](https://github.com/Unjuno/agent-interface/issues/17), [public transport boundary](../research/integration/mcp_transport_cancellation_20261016/README.md), [Fake X release-order counterexample](../research/live_control/fake_x_release_order_a01_20261018/REPORT.md), [queued-press caller regression](../research/integration/fake_x_single_writer_caller_20261018/README.md), [lease-expiry queued-press regression](../research/integration/press_lease_expiry_queued_server_mcp_20261018/README.md), [cancel-ack review fence](../research/integration/cancel_ack_review_fence_mcp_20261018/README.md), [#7034 requested process fence](../research/concurrency/x11_requested_process_fence_17_4d74_20261003/REPORT.md) | Preserve the false-clear and queued-DOWN outcomes. #9031 synchronously marks `review_required` at cancel acknowledgement (four related modules pass 61/61 normal and `-O`). #7034 already has a consumed Xvfb process-fence result: kill/reap before acceptance prevented the paused child’s suffix; do not rerun it. Next integrate an owned task-process boundary and separately confirmed cleanup through the selected standard caller, retaining an aborted call without completion receipt and UNKNOWN cleanup when confirmation fails. | #7034 used a prearmed cleanup scope; separate #7024 public cleanup-scope work ended `STOP / METHOD_FAIL`, so owner death does not establish public release-scope reconstruction. Fake X does not establish real X ordering, physical release deadline, task effect, or permanent backend/server nonresponse. Keep UNKNOWN under uncertainty; keep this lane distinct from target-generation checks unless the actual selected path is shared. |
| Target binding and feedback | [#5](https://github.com/Unjuno/agent-interface/issues/5), [visual agenda](ideas/visual-interface-agenda.md), [native dependency repair](../research/integration/compiled_native_dependency_repair_20261016/README.md), [current-main MCP lifecycle recheck](../research/integration/target_generation_mcp_caller_recheck_20261018/README.md), [capture-destroy caller regression](../research/integration/target_generation_capture_destroy_mcp_caller_20261018/README.md) | Fake X caller continuity, retained `window_generation`, stale-alias refusal, and source refusal when destruction occurs during capture are now covered. The next boundary is native X event coverage and capture-to-press continuity on an eligible real X target; until then, keep target identity and task effect as separate unknown gates. | Both rechecks use Fake X only; they do not prove real XID reuse, physical input, task effect, or a release deadline. Do not consume a WSLc allocation without a verified unused owner/allocation. |
| MAP01 response and recovery | [#59](https://github.com/Unjuno/agent-interface/issues/59), [live threat-guard PR family](ideas/map01-live-guard-evidence-family.md), [V15/controller selection](../research/integration/owned_service_session_20261016/README.md), [selected Backend/Executor adapter](../research/integration/owned_backend_adapter_20261016/README.md) | Six open PRs preserve distinct A01–A13 MAP01 threat-guard packets. First split is read-only audit of each packet's frozen source/raw and unresolved auditor finding; no allocation rerun. Then reconcile verified boundaries into the parent agenda and choose the next actual research condition. | Exact PR heads are 466–845 commits behind current main and have unresolved audit/review findings. Do not merge or close on title/age; do not rerun consumed live attempts. Each packet audit writes a distinct additive note; one integrator edits shared indexes. |
| Semantic recovery and application effects | [#57](https://github.com/Unjuno/agent-interface/issues/57), [finite role prototype](../research/integration/finite_role_recovery_convergence_20261016/README.md), [presentation failure custody](../research/integration/primary_presentation_convergence_20261016/README.md), [compiled timing receipt](../runtime/core_v1/COMPILED_GUI.md) | The bounded graph now retains observation adapter, accepted execution, effect-observation and verifier timing bounds, joined by action ID. Next connect this path through a supported standard caller with a qualified independent application-effect reader and bounded recovery. | The graph and timings are not exposed as a standard MCP tool; callbacks are trusted synchronous adapters. `TASK_SUCCEEDED` is not an independent task certificate, and timestamps do not qualify native/live latency or unblock synchronous I/O. |
| Matched efficiency and transfer | [#57](https://github.com/Unjuno/agent-interface/issues/57), [#2789](https://github.com/Unjuno/agent-interface/issues/2789), [Calc saved crosswalk](../research/live_control/calc_saved_convergence_20261016/README.md), [integration gates](INTEGRATION_PLAN.md) | Resolve a named accounting or supported-domain prerequisite, then measure matched tasks, correctness, all attempts, tokens/calls, latency and resources under qualified conditions. | Four saved familiar Calc cases and joint usage are not matched per-arm economics. Do not replay old allocations or transfer old-source PASS. |
| PR, branch and worktree custody | [Current open-PR metadata r8](maintenance/repository-inventory-20261018-r8.md), [convergence status](maintenance/consolidation-status-20261016.md), [MAP01 packet crosswalk](ideas/map01-live-guard-evidence-family.md), [event timing convergence](../research/integration/v39_event_timing_convergence_20261016/README.md) | Start with one family: six #59 live-threat-guard packets have exact heads, retained outcomes and read-only follow-up scopes in their crosswalk. For every candidate head, compare the current diff to main and establish unique evidence and actual owner/custody before merge, transfer, closure or ref removal. | Inventory metadata is not semantic review. Several old heads are hundreds of commits behind; preserve unique raw and owner changes. Do not delete a branch/worktree based only on closed/old/duplicate-looking status. |
| Local workspace artifacts | [Read-only custody census](maintenance/workspace-custody-census-20261019.md) | Take a small CSV batch and link each folder/file to its worker/session, Issue/PR, canonical evidence, and raw-result role; return reviewed rows with an evidence-backed disposition. | Census is local metadata only, not proof of ownership or staleness. Do not move/delete unreviewed or owner-unknown items; do not treat local artifacts as Git worktrees. |

## Execute and leave a usable result

1. Read the selected Issue/body/comments and relevant open/closed PRs; pin the
   source and choose the smallest check that changes an adoption decision.
2. Record narrow scope, branch and additive output through the existing owning
   surface. A claim comment is coordination, not an atomic resource lock.
3. Execute authorized local work. For a new live/formal run, confirm only the
   resources and unused allocation actually required. Do not revive historical
   reservations as universal blockers or start a consumed experiment again.
4. Preserve first outcomes, source, conditions, raw, relevant local check results
   and limits. Integrate subject to actual permissions/protection; optional CI
   queues and invented reviewer counts are not universal waits.
5. Return the result and next action to its owning question. Distinguish local
   construction, saved-result audit, main integration and live task success.

## Find prior evidence

The former map is preserved [verbatim as history](WORKER_WORK_MAP_HISTORY_20261016.md).
Its detailed links remain useful; its dated next actions are not fresh assignments.
Use [consolidation status](maintenance/consolidation-status-20261016.md) for PR
family dispositions and [evidence map](EVIDENCE_MAP.md) for scientific records.
Sparse checkouts may need exact tracked fixtures materialized with
`git restore --ignore-skip-worktree-bits --worktree -- <path>`; never regenerate
missing historical fixtures by rerunning a consumed producer.
