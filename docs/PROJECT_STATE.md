# Project state and work order

Updated 2026-11-22 from current `main` `48ef3e498b287a69b68e3e6912a43db2acb3551b`.
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
| Public standard caller / task outcome | Fresh fixture R06 and R08 both completed one public Win32 action, exact `interface_results` lookup, same-generation before/after public observations, verified release and a 2 s/78-sample horizon, with an independent delayed fixture score. R08's journal was reconstructed offline through the repairs merged by PR #10451 at this main. Public `task_success` remains `null`. | **Open.** Next exercise an independently frozen recovery task through the standard caller. R08 is one no-provider fixture sample, not an expired delayed-operation test, MAP01 result, or reliability estimate. See [R08](../research/integration/win32_recorded_task_effect_r08_20261122/README.md), [R06](../research/integration/win32_public_task_effect_r06_20261122/README.md), and [R07 stop](../research/integration/win32_recorded_task_effect_r07_20261122/README.md). |
| Issue #57 integrated efficiency | Main has the comparison ledger, recorded-caller adapter, effect attribution, completed-action handoff, and public observation identity/PNG validation. R08 reconstructs into the measured-run/effect handoff; it has no provider or model accounting. | **Open.** No matched live A/B/C block with complete provider-attempt/token accounting, task correctness, latency, and cleanup exists. R06/R08 are separate fixture samples and cannot supply comparative efficiency or recovery reliability. See [Issue #57 next gates](maintenance/issue57-next-gates-20261121.md), [R08](../research/integration/win32_recorded_task_effect_r08_20261122/README.md), and [R02 synthetic handoff](../research/integration/standard_mcp_task_ledger_57_v1/public_win32_effect_pair_handoff_r02_20261122/RESULT.md). |
| Recovery and repeated reliability | Win32 synthetic failure-path contracts and MAP01 native attempts include release/horizon evidence. MAP01 R196/R197 each observed the HUD effect, but neither has an independently scored task-success result or matched efficiency accounting. Calc G10 has retained fixture/artifact and synthetic composition evidence. | **Open.** Freeze one standard-caller recovery task and independent scorer, distinguish UNKNOWN/release/task outcome, and repeat fresh attempts under pinned conditions. Do not combine fixture, MAP01, and Calc results into one reliability rate. See [R196/R197 and prior records](../ROADMAP.md) and the [G10 crosswalk](../research/integration/calc_g10_current_main_crosswalk_20261027.md). |
| Distributable runtime | Portable runtime packaging and Ubuntu WSL startup/CLI checks exist; Research Preview runner and fixture checks are also retained. | **Partial.** A distributable artifact is not the same as supported-host acceptance or preview graduation. Close the #58 setup, audit, golden-run, and live-audit gates before calling the runtime release-ready. |

## Repository organization

- The latest GitHub membership receipt is r164: **1,640 open Issues and
  405 open PRs**, collected against unchanged main
  `48ef3e498b287a69b68e3e6912a43db2acb3551b`.
  Exact comparison with r152/r157 found no additions; Issues #7748/#7765/#7817
  and PRs #7968/#8181/#10227 are removed. This reconciles the two-PR delta
  previously noted at r163. Counts are inventory, not semantic triage. The full
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

1. Continue family-by-family semantic triage and custody reconciliation using
   the fresh r164 membership baseline; do not infer disposition from counts.
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
