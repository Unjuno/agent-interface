# Worker work map

2026-10-18. Current main is `f4cd5577ef57a01d7b25a389d877c9d1b3ab9d21`.
The latest complete membership snapshot is [open Issues r7](maintenance/open-issues-20261018-r7.csv)
(1,676) and [open PRs r7](maintenance/open-prs-20261018-r7.csv) (514); membership
is unchanged from r6. See [r76 consolidation status](maintenance/consolidation-status-20261016.md)
for the snapshot hashes and scope. Start from [current goal](CURRENT_GOAL.md), choose one finite item
below, and verify its current Issue, source and ownership. This map is navigation;
it adds no assignment, resource grant, reviewer quota or all-workers waiting gate.

## Choose work

| Scope | Existing question / evidence | Next finite deliverable | Collision boundary |
|---|---|---|---|
| Repository and ideas | [Consolidation plan](REPOSITORY_CONSOLIDATION.md), [r76 current status](maintenance/consolidation-status-20261016.md), [idea index](ideas/README.md), [r7 Issue/PR inventory](maintenance/repository-inventory-20261018-r7.md) | Choose a research family by its question and evidence, then read the current Issue, necessary comments, related open/closed PRs and exact current heads. Add a concise hypothesis/evidence/residual/next-test entry; mark missing evidence `unverified`. Treat the 514 PR inventory as untriaged except where a disposition is linked. | Declare disjoint Issue/PR numbers, code area and output file before parallel work. Separate families may proceed independently; serialize edits to shared indexes. Do not use age, draft state or empty assignee fields as closure evidence. |
| Input authority and release | [#17](https://github.com/Unjuno/agent-interface/issues/17), [public transport boundary](../research/integration/mcp_transport_cancellation_20261016/README.md), [Fake X release-order counterexample](../research/live_control/fake_x_release_order_a01_20261018/REPORT.md), [queued-press caller regression](../research/integration/fake_x_single_writer_caller_20261018/README.md), [lease-expiry queued-press regression](../research/integration/press_lease_expiry_queued_server_mcp_20261018/README.md) | Preserve the false-clear schedules and queued-DOWN cancel/expiry outcomes. PR #9027 requires review after an execution failure so the still-live alias cannot be reused; next connect single-authority writer retirement/fencing and late-send rejection through the selected caller, with bounded barriers and no replay. | Fake X remains a model. The new regression shows an already-queued DOWN can arrive after lease expiry and cleanup waits for the fixture to resume. No real X ordering, physical release deadline, task effect, or permanent backend/server nonresponse guarantee is established; uncertainty remains UNKNOWN. Keep this lane distinct from target-generation checks unless the actual selected code path is shared. |
| Target binding and feedback | [#5](https://github.com/Unjuno/agent-interface/issues/5), [visual agenda](ideas/visual-interface-agenda.md), [native dependency repair](../research/integration/compiled_native_dependency_repair_20261016/README.md), [current-main MCP lifecycle recheck](../research/integration/target_generation_mcp_caller_recheck_20261018/README.md), [capture-destroy caller regression](../research/integration/target_generation_capture_destroy_mcp_caller_20261018/README.md) | Fake X caller continuity, retained `window_generation`, stale-alias refusal, and source refusal when destruction occurs during capture are now covered. The next boundary is native X event coverage and capture-to-press continuity on an eligible real X target; until then, keep target identity and task effect as separate unknown gates. | Both rechecks use Fake X only; they do not prove real XID reuse, physical input, task effect, or a release deadline. Do not consume a WSLc allocation without a verified unused owner/allocation. |
| MAP01 response and recovery | [#59](https://github.com/Unjuno/agent-interface/issues/59), [live threat-guard PR family](ideas/map01-live-guard-evidence-family.md), [V15/controller selection](../research/integration/owned_service_session_20261016/README.md), [selected Backend/Executor adapter](../research/integration/owned_backend_adapter_20261016/README.md) | Six open PRs preserve distinct A01–A13 MAP01 threat-guard packets. First split is read-only audit of each packet's frozen source/raw and unresolved auditor finding; no allocation rerun. Then reconcile verified boundaries into the parent agenda and choose the next actual research condition. | Exact PR heads are 466–845 commits behind current main and have unresolved audit/review findings. Do not merge or close on title/age; do not rerun consumed live attempts. Each packet audit writes a distinct additive note; one integrator edits shared indexes. |
| Semantic recovery and application effects | [#57](https://github.com/Unjuno/agent-interface/issues/57), [finite role prototype](../research/integration/finite_role_recovery_convergence_20261016/README.md), [presentation failure custody](../research/integration/primary_presentation_convergence_20261016/README.md) | Connect a selected-document effect reader and bounded recovery through the actual caller. Retain unknown partial effects and refuse unsafe resend. | A synthetic file oracle/prototype is not a qualified editor/application adapter. Caller/backend changes can overlap the release lane. |
| Matched efficiency and transfer | [#57](https://github.com/Unjuno/agent-interface/issues/57), [#2789](https://github.com/Unjuno/agent-interface/issues/2789), [Calc saved crosswalk](../research/live_control/calc_saved_convergence_20261016/README.md), [integration gates](INTEGRATION_PLAN.md) | Resolve a named accounting or supported-domain prerequisite, then measure matched tasks, correctness, all attempts, tokens/calls, latency and resources under qualified conditions. | Four saved familiar Calc cases and joint usage are not matched per-arm economics. Do not replay old allocations or transfer old-source PASS. |
| PR, branch and worktree custody | [Open PR inventory r7](maintenance/repository-inventory-20261018-r7.md), [convergence status](maintenance/consolidation-status-20261016.md), [MAP01 packet crosswalk](ideas/map01-live-guard-evidence-family.md), [event timing convergence](../research/integration/v39_event_timing_convergence_20261016/README.md) | Current r7 contains 514 open PRs. Start with one family: six #59 live-threat-guard packets now have exact heads, retained outcomes and read-only follow-up scopes. After those audits, compare any candidate head to current main and prove unique evidence/ownership before proposing merge, transfer, closure or ref removal. | Current PR list is metadata, not semantic review. Several old heads are hundreds of commits behind; preserve unique raw and owner changes. Do not delete a branch/worktree based only on closed/old/duplicate-looking status. |

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
