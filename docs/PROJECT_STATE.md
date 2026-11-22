# Project state and work order

Updated 2026-11-22 from current `main` `f5c87f4bef26be604bb6872e63ee2274d1c9bbd3`.
This page is the short project-wide status index. It points to the detailed
receipts; it does not replace their raw evidence or promote a partial result.

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
| Research Preview / Issue #58 | Acceptance runner repair is merged. Frozen RC1 launcher preflight passes 19/19 and reuses its venv. Doctor is 12/15 because supported-host Windows Codex CLI JS and WSL Chromium prerequisites are absent. | **Open.** Verify the supported Windows/WSL bridge and Chromium, then complete the retained audit, fresh no-retry golden run, and `audit-live`. See [Roadmap](../ROADMAP.md) and [the current-main R01 packet](../research/integration/research_preview_rc1_setup_doctor_r05_20261121/current-main-runner-r01/RESULT.md). |
| Public standard caller / task outcome | Fresh fixture R06 on current main completed one public action, exact `interface_results` lookup, before/after public observations on the same generation, verified release and 2 s/78-sample horizon, and an independent delayed-effect score. Public `task_success` remains `null`. The offline action-ID adapter seam is fixed in the current local candidate; its 68-test suites pass normally and under `-O`. | **Open.** Merge the identity join, then run a fresh recorded caller experiment with call-boundary capture and build the canonical measured-run/effect receipt. R06 cannot be retrofitted with missing recorder boundaries. Then exercise a separately frozen recovery task. R06 is one fixture sample, not MAP01 or reliability evidence. See [R06](../research/integration/win32_public_task_effect_r06_20261122/README.md) and [public action ID join R01](../research/integration/standard_mcp_task_ledger_57_v1/public_action_id_join_r01_20261122/README.md). |
| Issue #57 integrated efficiency | Main has the comparison ledger, recorded-caller adapter, effect attribution, completed-action handoff, and public observation identity/PNG validation. R06 demonstrates a live fixture capture/result/effect sequence, but its raw calls are not yet ingested into the canonical measured-run. | **Open.** No matched live A/B/C block with complete provider-attempt/token accounting, task correctness, latency, and cleanup exists. R06 uses no provider/model and cannot supply efficiency or recovery reliability. See [Issue #57 next gates](maintenance/issue57-next-gates-20261121.md), [R02](../research/integration/standard_mcp_task_ledger_57_v1/public_win32_effect_pair_handoff_r02_20261122/RESULT.md), and [R06](../research/integration/win32_public_task_effect_r06_20261122/README.md). |
| Recovery and repeated reliability | Win32 synthetic failure-path contracts and MAP01 native attempts include release/horizon evidence. MAP01 R196/R197 each observed the HUD effect, but neither has an independently scored task-success result or matched efficiency accounting. Calc G10 has retained fixture/artifact and synthetic composition evidence. | **Open.** Freeze one standard-caller recovery task and independent scorer, distinguish UNKNOWN/release/task outcome, and repeat fresh attempts under pinned conditions. Do not combine fixture, MAP01, and Calc results into one reliability rate. See [R196/R197 and prior records](../ROADMAP.md) and the [G10 crosswalk](../research/integration/calc_g10_current_main_crosswalk_20261027.md). |
| Distributable runtime | Portable runtime packaging and Ubuntu WSL startup/CLI checks exist; Research Preview runner and fixture checks are also retained. | **Partial.** A distributable artifact is not the same as supported-host acceptance or preview graduation. Close the #58 setup, audit, golden-run, and live-audit gates before calling the runtime release-ready. |

## Repository organization

- The latest full GitHub membership receipt is r163: **1,640 open Issues and
  407 open PRs** at its recorded checkpoint. A live CLI recount while writing
  this page returned **1,640 Issues and 405 PRs**. The two-PR delta has not yet
  been reconciled by exact ID set, so r163 remains the latest complete
  membership audit. Counts are inventory, not semantic triage. The full
  family-level routing map is the dated [r160 crosswalk](maintenance/idea-index-crosswalk-20261121-r160.md); targeted checks are recorded in [the organization recheck](maintenance/targeted-organization-recheck-20261122.md).
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

1. Finish a fresh project inventory against the latest main and GitHub state;
   update dated receipts rather than silently treating r160/r163 as current.
2. Convert the R06 live public caller raw records to the canonical measured-run
   and task-effect receipt, preserving the live `task_success=null` fact.
3. Freeze one finite standard-caller recovery experiment and run its local
   negative controls before any live dispatch; preserve every attempt.
4. Run the matched all-attempt efficiency block only after the measurement path
   can account for every provider attempt and all arms' task outcomes.
5. Close the supported-host Research Preview acceptance gates and verify the
   portable runtime artifact on its declared hosts.
6. Reconcile the broader Issue/PR/worktree queue family by family, retaining
   ideas that lack evidence for closure and resolving custody before deletion.

The overall goal remains active until these gates have direct evidence. Current
source-only and fixture results are useful progress but do not satisfy the live
research or release gates.

## Source records

- [Current goal](CURRENT_GOAL.md)
- [Roadmap](../ROADMAP.md)
- [Repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md)
- [Issue #57 next gates](maintenance/issue57-next-gates-20261121.md)
- [Latest inventory receipt r163](maintenance/repository-inventory-recheck-20261122-r163.md)
- [Worker work map](WORKER_WORK_MAP.md)
