# Worker work map

2026-10-19 update. Cursor-paginated GitHub reads returned 1,675 open Issues and
514 open PRs against main `34344716c62d04d237a149fb97aabebd56944ca8`. Against
[r13](maintenance/repository-inventory-20261019-r13.md), both ID sets are unchanged.
See [r14 inventory](maintenance/repository-inventory-20261019-r14.md) for timestamp,
CSV checksums and exact metadata. This is not semantic review or
proof of current ownership. Earlier snapshots are historical. Begin with
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
| Repository and ideas | [Consolidation plan](REPOSITORY_CONSOLIDATION.md), [r76 historical status](maintenance/consolidation-status-20261016.md), [idea index](ideas/README.md), [research Issue index](RESEARCH_ISSUE_INDEX.md), [r14 inventory](maintenance/repository-inventory-20261019-r14.md), [evidence-admission family](ideas/evidence-admission-family.md) | The #5314/#5305/#5339 family now has a cross-linked hypothesis/result map. Next finite step: verify readback custody for #5305's held-out T1 raw without modifying it; retain STOP if unavailable, then define a distinct held-out comparison before any new run. | Number-only scans of one idea directory are incomplete because the research Issue index and evidence map are separate. Declare disjoint Issue/PR numbers and output paths before parallel work. Family notes may proceed independently; serialize edits to shared indexes. Do not use age, draft state or empty assignee fields as closure evidence. |
| Input authority and release | [#17](https://github.com/Unjuno/agent-interface/issues/17), [public transport boundary](../research/integration/mcp_transport_cancellation_20261016/README.md), [Fake X release-order counterexample](../research/live_control/fake_x_release_order_a01_20261018/REPORT.md), [queued-press caller regression](../research/integration/fake_x_single_writer_caller_20261018/README.md), [lease-expiry queued-press regression](../research/integration/press_lease_expiry_queued_server_mcp_20261018/README.md), [cancel-ack review fence](../research/integration/cancel_ack_review_fence_mcp_20261018/README.md), [#7034 requested process fence](../research/concurrency/x11_requested_process_fence_17_4d74_20261003/REPORT.md), [#7041 prearmed-scope transfer result](https://github.com/Unjuno/agent-interface/blob/main/research/concurrency/x11_crash_cleanup_scope_a02_17_5ce3_20261003/REPORT.md), [owned guarded MCP process integration](../research/integration/owned_guarded_mcp_process_20261019/README.md), [#9047 standard-caller composition](../research/integration/standard_caller_release_order_composition_20261019/README.md), [WSLc A11 blocked-owner XRes/release result](../research/integration/xres_blocked_owner_release_a11_20261019/README.md) | The standard MCP owner-process path records exact held-input obligations and keeps release UNKNOWN when disconnect/readback ordering is ambiguous. Merged [#9047](https://github.com/Unjuno/agent-interface/pull/9047) adds a composed Fake X regression for injected owner/XRes retirement, mocked empty cleanup readback, and a late old-connection DOWN; cancel and terminal state refuse release confirmation, success, and replay. Five selected owner/cancel/target-generation tests pass in normal and `-O`; see the retained report and raw logs. Separate WSLc A11 Xvfb evidence passed 8/8, but is fixture-level and does not validate this standard caller path. Live X server ordering, release deadlines, task effect and bounded recovery remain open; live qualification requires a verified unused allocation. | #9047's late queued DOWN is an adversarial Fake X schedule, not proof that a live X server executes it. #7041 is research instrumentation, not a public recovery API or general unknown-key reconstruction; its original #7024 predecessor remains an immutable method STOP. A11 used responsive Xvfb and does not establish physical desktop, XWayland, permanently unresponsive server, target incarnation, task effect, or physical deadline. Nested stdio tests were excluded because the child interpreter could not load this host's temporary MCP dependency. Keep #17 open and UNKNOWN under uncertainty. |
| Target binding and feedback | [#5](https://github.com/Unjuno/agent-interface/issues/5), [visual agenda](ideas/visual-interface-agenda.md), [native dependency repair](../research/integration/compiled_native_dependency_repair_20261016/README.md), [current-main MCP lifecycle recheck](../research/integration/target_generation_mcp_caller_recheck_20261018/README.md), [capture-destroy caller regression](../research/integration/target_generation_capture_destroy_mcp_caller_20261018/README.md) | Fake X caller continuity, retained `window_generation`, stale-alias refusal, and source refusal when destruction occurs during capture are now covered. The next boundary is native X event coverage and capture-to-press continuity on an eligible real X target; until then, keep target identity and task effect as separate unknown gates. | Both rechecks use Fake X only; they do not prove real XID reuse, physical input, task effect, or a release deadline. Do not consume a WSLc allocation without a verified unused owner/allocation. |
| MAP01 response and recovery | [#59](https://github.com/Unjuno/agent-interface/issues/59), [live threat-guard PR family](ideas/map01-live-guard-evidence-family.md), [V15/controller selection](../research/integration/owned_service_session_20261016/README.md), [selected Backend/Executor adapter](../research/integration/owned_backend_adapter_20261016/README.md) | Six open PRs preserve distinct A01–A13 MAP01 threat-guard packets. First split is read-only audit of each packet's frozen source/raw and unresolved auditor finding; no allocation rerun. Then reconcile verified boundaries into the parent agenda and choose the next actual research condition. | Exact PR heads are 466–845 commits behind current main and have unresolved audit/review findings. Do not merge or close on title/age; do not rerun consumed live attempts. Each packet audit writes a distinct additive note; one integrator edits shared indexes. |
| Semantic recovery and application effects | [#57](https://github.com/Unjuno/agent-interface/issues/57), [finite role prototype](../research/integration/finite_role_recovery_convergence_20261016/README.md), [presentation failure custody](../research/integration/primary_presentation_convergence_20261016/README.md), [compiled timing receipt](../runtime/core_v1/COMPILED_GUI.md) | The bounded graph now retains observation adapter, accepted execution, effect-observation and verifier timing bounds, joined by action ID. Next connect this path through a supported standard caller with a qualified independent application-effect reader and bounded recovery. | The graph and timings are not exposed as a standard MCP tool; callbacks are trusted synchronous adapters. `TASK_SUCCEEDED` is not an independent task certificate, and timestamps do not qualify native/live latency or unblock synchronous I/O. |
| Matched efficiency and transfer | [#57](https://github.com/Unjuno/agent-interface/issues/57), [#2789](https://github.com/Unjuno/agent-interface/issues/2789), [Calc saved crosswalk](../research/live_control/calc_saved_convergence_20261016/README.md), [integration gates](INTEGRATION_PLAN.md) | Resolve a named accounting or supported-domain prerequisite, then measure matched tasks, correctness, all attempts, tokens/calls, latency and resources under qualified conditions. | Four saved familiar Calc cases and joint usage are not matched per-arm economics. Do not replay old allocations or transfer old-source PASS. |
| PR, branch and worktree custody | [Current open-PR metadata r14](maintenance/repository-inventory-20261019-r14.md), [convergence status](maintenance/consolidation-status-20261016.md), [MAP01 packet crosswalk](ideas/map01-live-guard-evidence-family.md), [event timing convergence](../research/integration/v39_event_timing_convergence_20261016/README.md) | Start with one family: six #59 live-threat-guard packets have exact heads, retained outcomes and read-only follow-up scopes in their crosswalk. For every candidate head, compare the current diff to main and establish unique evidence and actual owner/custody before merge, transfer, closure or ref removal. | Inventory metadata is not semantic review. Several old heads are hundreds of commits behind; preserve unique raw and owner changes. Do not delete a branch/worktree based only on closed/old/duplicate-looking status. |
| Local workspace artifacts | [Read-only custody census](maintenance/workspace-custody-census-20261019.md) | Take a small CSV batch and link each folder/file to its worker/session, Issue/PR, canonical evidence, and raw-result role; return reviewed rows with an evidence-backed disposition. | Census is local metadata only, not proof of ownership or staleness. Do not move/delete unreviewed or owner-unknown items; do not treat local artifacts as Git worktrees. |

**2026-10-19 standard-caller release-order composition:** The added [Fake X
composition](../research/integration/standard_caller_release_order_composition_20261019/README.md)
passes in normal and optimized Python. Even with mocked XRes disappearance and a
fresh-cleanup `readback_verified` receipt, the delayed old-connection `KeyPress`
left the modeled key down; the standard cancel and terminal reports stayed
UNKNOWN, replay-disabled, and without task success. This supports the existing
UNKNOWN policy but does not establish the real server ordering or release bound.
Next discriminator remains a real-server queue fence under an explicitly unused
eligible allocation.

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
