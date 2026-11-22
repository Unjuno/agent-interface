# Project state and work order

Updated 2026-11-23 from current `main` `b0bc13d71fd204e39d040584c2e3e9207a7879dd`.
This page is the short project-wide status index. It points to the detailed
receipts; it does not replace their raw evidence or promote a partial result.

## Latest #57 composition result — 2026-11-23

The current-main candidate composes public MCP observe/dispatch/exact-result
lookup with automatic recovery and an independent task oracle. It allows task
verification after automatic completion recovery only when the action remains
UNKNOWN, recovery separately confirms release, and the matching late-input
horizon is verified. The positive composition and unknown-custody negative
control pass 2/2 normally and under `-O`; all external effects are fixtures.
This does not establish native task effect, reliability, efficiency, MAP01, or
Research Preview acceptance. Keep #57 and the project goal open. See the
[R01 packet](../research/integration/standard_mcp_task_ledger_57_v1/current_main_public_recovered_caller_r01_20261123/RESULT.md).

## What the project is trying to finish

The project has two connected tracks:

1. **A distributable public runtime:** supported-host setup, bounded and
   inspectable public control, reliable task effects and recovery, and a
   repeatable acceptance path suitable for Research Preview.
2. **Evidence that the runtime is useful and safe:** matched lifecycle cost
   comparisons, independently scored task outcomes, recovery/reliability
   measurements, and preserved experiment custody.

Passing unit tests, fake backends, fixture effects, and a packaged CLI are
necessary pieces. They do not by themselves establish live control, task
success, comparative efficiency, reliability, or preview readiness.

## Gate status

| Gate | Current evidence | Status and remaining proof |
| --- | --- | --- |
| Research Preview / Issue #58 | Frozen RC1 R01 passed launcher preflight 19/19; doctor was 12/15. Current-main R02 passed launcher preflight 19/19 and held at explicit dependency-install opt-in; its supplemental doctor was 12/15. PR #10463 merged as `d5ada452`. Its WSL R06 package build included the 29-file frozen archive; extracted retained audit passed 29/29 and reported seven later source differences. | **Open.** This fixes the retained-audit source custody and proves package construction on WSL; supported-host doctor, fresh no-retry golden run, and `audit-live` remain unverified. The host recheck found no WSL Chromium and no configured Windows Codex CLI JS; Windows Node/Chrome are present, but the bridge is untested. No install or live run occurred. See [R06](../research/integration/research_preview_retained_source_audit_r01_20261122/supplemental-linux-build-r06-20261122/RESULT.md), [R02](../research/integration/research_preview_rc1_setup_doctor_r05_20261121/current-main-prefix-r02-20261122/RESULT.md), and [frozen RC1 R01](../research/integration/research_preview_rc1_setup_doctor_r05_20261121/current-main-runner-r01/RESULT.md). |
| Public standard caller / task outcome | Fresh fixture R06 and R08 each completed one public Win32 action, exact `interface_results` lookup, same-generation before/after public observations, verified release and a 2 s/78-sample horizon, with an independent delayed fixture score. R08's journal was reconstructed offline through the repairs merged by PR #10451. A separate current-main local composition R01 confirms that independently verified task success can remain distinct from graph completion after recovery, while the source action stays UNKNOWN/null and replay is denied. | **Open.** The R01 callbacks are synthetic; still run a separately frozen public standard-caller recovery task with an independent scorer and task effect. R06/R08 are no-provider fixture samples, not MAP01 results or reliability estimates. See [recovered-caller R01](../research/integration/standard_mcp_task_ledger_57_v1/current_main_recovered_caller_task_oracle_r01_20261122/RESULT.md), [R08](../research/integration/win32_recorded_task_effect_r08_20261122/README.md), [R06](../research/integration/win32_public_task_effect_r06_20261122/README.md), and [R07 stop](../research/integration/win32_recorded_task_effect_r07_20261122/README.md). |
| Issue #57 integrated efficiency | Main has the comparison ledger, recorded-caller adapter, effect attribution, completed-action handoff, and public observation identity/PNG validation. R08 reconstructs into the measured-run/effect handoff; it has no provider or model accounting. | **Open.** No matched live A/B/C block with complete provider-attempt/token accounting, task correctness, latency, and cleanup exists. R06/R08 are separate fixture samples and cannot supply comparative efficiency or recovery reliability. See [Issue #57 next gates](maintenance/issue57-next-gates-20261121.md), [R08](../research/integration/win32_recorded_task_effect_r08_20261122/README.md), and [R02 synthetic handoff](../research/integration/standard_mcp_task_ledger_57_v1/public_win32_effect_pair_handoff_r02_20261122/RESULT.md). |
| Recovery and repeated reliability | R16 resolved the exact R14 durable UNKNOWN custody record through one public Win32 orphan-recovery call on a distinct fresh generation. Its native release/readback and 2 s horizon passed; source task outcome remained UNKNOWN, with no task dispatch or effect. MAP01 R196/R197 each observed the HUD effect, but neither has an independently scored task-success result or matched efficiency accounting. Calc G10 has retained fixture/artifact and synthetic composition evidence. | **Open.** R16 closes only this scoped custody recovery case. Next freeze a standard-caller recovery task with independent scoring, preserve UNKNOWN/release/task-outcome distinctions, and repeat fresh attempts under pinned conditions. Do not combine fixture, MAP01, and Calc results into one reliability rate. See [R16](../research/integration/win32_native_sendinput_recovery_20261122_r16/RESULT.md), [R196/R197 and prior records](../ROADMAP.md), and the [G10 crosswalk](../research/integration/calc_g10_current_main_crosswalk_20261027.md). |
| Distributable runtime | On `d5ada452` (an ancestor of current main `cd708f52`), the 21-test suite passed on Windows and Ubuntu WSL, normal and `-O`; later main commits are limited to evidence/documentation updates. The WSL Research Preview package build and extracted retained audit also passed. | **Partial.** Construction and basic CLI contracts pass; live native input, permissions, public artifact publication, and the remaining #58 supported-host/golden-run gates are unverified. |

## Repository organization

- The latest GitHub membership receipt is r165: **1,640 open Issues and
  405 open PRs**, collected against unchanged main
  `d5ada452527f97b90c3265966a6aebd7743cf483`. The exact sorted-ID hashes
  match r164; #10463 opened after r164 and merged before r165; it was absent from both snapshots, so no net queue delta
  change. See [r165](maintenance/repository-inventory-recheck-20261122-r165.md).
  Exact comparison with r152/r157 found no additions; Issues #7748/#7765/#7817
  and PRs #7968/#8181/#10227 are removed. This reconciles the two-PR delta
  previously noted at r163. Counts are inventory, not semantic triage. The full
  family-level routing map is the dated [r160 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md); targeted checks are recorded in [the organization recheck](maintenance/targeted-organization-recheck-20261122.md).
  A count-only GraphQL read at 2026-11-22 14:55 UTC against current main
  `cd708f52` returned 1,640 open Issues and 405 open PRs; exact membership and
  semantic dispositions were not rechecked.
- Do not close or merge items based only on age, unchanged inventory, or green
  checks. PR #10144 remains a Draft research prototype; Issue #7773 remains on
  feasibility HOLD. Other items require their own evidence/custody review.
- The last custody snapshot found **15 registered worktrees: 10 clean and 5
  dirty**. It also identified 61 unique files in root `outputs/`; preserve all
  unique experiment data. The 16-file ledger output directory is byte-identical
  to tracked blobs, but its attempted deletion was rejected and it remains.
  See [worktree custody](maintenance/worktree-custody-recheck-20261122.md).
- Cleanup is therefore **in progress, not complete**: reconcile branch/PR
  reachability, inspect dirty worktrees and raw artifacts by path and hash,
  route every open item to an evidence-backed disposition, then remove only
  verified duplicates whose custody and references are resolved.

## Execution order

1. Continue family-by-family semantic triage and custody reconciliation using
   the r165 full membership baseline; do not infer disposition from counts.
2. With R08 now reconstructed and its adapter repairs merged, freeze one finite
   standard-caller recovery experiment, pass its local negative controls, then
   run it while preserving public `task_success` separately from independently
   scored effect and eligibility. Preserve every attempt.
3. Run the matched all-attempt efficiency block only after the measurement path
   can account for every provider attempt and all arms' task outcomes.
4. Close the supported-host Research Preview acceptance gates and verify the
   portable runtime artifact on its declared hosts.
5. Reconcile the broader Issue/PR/worktree queue family by family, retaining
   ideas that lack evidence for closure and resolving custody before deletion.

The overall goal remains active until these gates have direct evidence. Current
source-only and fixture results are useful progress but do not satisfy the live
research or release gates.

## Source records

- [Current goal](CURRENT_GOAL.md)
- [Roadmap](../ROADMAP.md)
- [Repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md)
- [Issue #57 next gates](maintenance/issue57-next-gates-20261121.md)
- [Latest inventory receipt r164](maintenance/repository-inventory-recheck-20261122-r164.md)
- [Worker work map](WORKER_WORK_MAP.md)
