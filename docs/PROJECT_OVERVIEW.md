# Agent Interface project overview

**Snapshot:** current main `beba1903d7ddd9d5c9e810bc35edd1db3772286d` (2026-11-23), after PR #10520. This is the short, project-wide orientation page. Detailed experiment records, failure history, and raw evidence remain in their existing locations.

## Purpose

Agent Interface aims to make computer control more effective while preserving the rich model's semantic understanding and strategy. Bounded local mechanisms may reduce repeated observation, waiting, and recovery when fresh evidence supports them. Correctness, authority, observable task effect, release, and finite recovery remain required; a faster but less reliable path is not a win.

The public product and research program are connected but distinct:

1. **A distributable runtime** must install and run on declared hosts, expose bounded inspectable control, preserve authority and release semantics, and pass a reproducible acceptance path.
2. **Research evidence** must show that the integrated route solves real tasks safely and improves end-to-end cost against a strong simple baseline. Unit tests, fake backends, synthetic composition, and package construction each prove only their recorded scope.
3. **Repository organization** must make work, evidence, ownership, and disposition discoverable without deleting viable ideas or closing Issues merely to reduce counts.

## Current state

At this snapshot, Issues [#53](https://github.com/Unjuno/agent-interface/issues/53), [#56](https://github.com/Unjuno/agent-interface/issues/56), [#57](https://github.com/Unjuno/agent-interface/issues/57), [#58](https://github.com/Unjuno/agent-interface/issues/58), and [#59](https://github.com/Unjuno/agent-interface/issues/59) remain open. PRs [#10515](https://github.com/Unjuno/agent-interface/pull/10515) through [#10520](https://github.com/Unjuno/agent-interface/pull/10520) are merged and represented in main. The last complete membership receipt, r175, recorded 1,640 open Issues and 404 open PRs at its stated main revision; it is a dated baseline, not a live count for this snapshot. The full queue has not been semantically re-triaged.

| Area | What is established | What remains open |
|---|---|---|
| Integrated caller and compiled GUI route (#53, #56, #57) | The earlier caller-v3-to-compiled-GUI synthetic composition remains in main. PR #10518 adds the exact Chromium V5 point-mint method and real handle store to the caller-v3/compiled-GUI Fake-only composition. Its positive and changed-generation cases pass 25/25 related tests in both normal and optimized Python; the changed-generation case retains the completed prefix and refuses the next input. PR #10520 adds a local Edge R09 packet, based on current main and using real screenshots/Windows OCR plus loopback task scoring; positive and changed-generation cases pass in normal and `-O` modes with retained raw evidence. | R09 is a headless Edge/CDP fixture, not OS input or a live provider/app workflow. It does not prove physical release, repeated reliability, current-main matched economics, Calc/MAP01 transfer, or a distributable runtime. The older three-arm result remains useful historical evidence but is not a current-main repetition. |
| Standard caller, effect, release, and recovery (#57) | R41/R42 each recorded one public recovered-task success on a fresh HWND/PID generation while the expired source stayed UNKNOWN and replay-denied. MAP01 R157/R158/R161 add scoped native release/horizon and independently checked 50→49 task-effect evidence. E01/E02 cover exception-to-fresh-recovery composition with fake producer/supervisor; 122 tests pass in normal and `-O`. | These trials do not estimate reliability, prove same-window or arbitrary-app continuation, or measure #57 efficiency. R160 runner failure and R156 exception-path UNKNOWN remain retained; E01/E02 have no native producer/recovery or physical two-second horizon. Preserve UNKNOWN and all stopped/failed outcomes. See [R160/R161](../research/integration/map01_recovery_deep_trace_r160_r161_20261113.md) and [R153–R156](../research/integration/map01_recovery_deep_trace_r153_r156_20261113.md). |
| Research Preview (#58) | A WSL package build and frozen-source retained audit passed; setup/launcher checks have partial coverage. | Supported-host readiness is incomplete. The current records do not establish the full doctor, fresh no-retry live run, final live audit, or browser-to-runtime control on the declared host. |
| Real-time control / MAP01 (#59) | R153/R154 and R157/R158/R161 contain scoped native Win32 recovery, release/horizon and task-effect results. Current-main R01 found no GZDoom in six standard paths, PATH, process table, or uninstall registry; R02 found no GZDoom/IWAD filename in five existing user roots. | No integrated threat-exposure pass or MAP01 completion is established. R153 stopped before input; R156 is FAIL/UNKNOWN; R160 is a runner failure. R02 did not search the full disk. Reacquire the isolated executable/assets before a fresh frozen attempt; do not install or download them as incidental setup. See [R02](../research/integration/map01_expanded_target_search_current_main_r02_20261123/RESULT.md), [R153–R156](../research/integration/map01_recovery_deep_trace_r153_r156_20261113.md), and [R160/R161](../research/integration/map01_recovery_deep_trace_r160_r161_20261113.md). |
| Runtime distribution | Deterministic package construction and several startup/CLI contracts have passed on recorded hosts. | Publicly obtainable artifact plus declared-host live authority/input behavior and complete acceptance remain unverified. |
| Issue/PR and local artifact organization | Organization plans, evidence indices, historical inventories, and targeted family dispositions exist. The latest complete r175 membership receipt records 1,640 open Issues and 404 open PRs at main `acce16071b604fa8c06287d0b71d27addeccf481`; relative to r173, only PR #7760 left the open set. | That receipt predates this snapshot and reports membership only. Semantic disposition remains incomplete; the issue/PR crosswalk is r160, not whole-queue triage. Worktree/output custody also has unresolved entries. See [r175](maintenance/repository-inventory-recheck-20261123-r175.md). |

## Work order

1. **Protect the live research question.** Follow #59's requirement to resolve the real-time threat-response gap before spending a research block on presentation or broad packaging. Reuse the retained passes and failures; the bounded current-main search did not find GZDoom in standard locations. Reacquire the exact owned executable and IWAD before a fresh run, then freeze the current-main path and stop rule. Do not substitute another target or infer completion from movement-only effects.
2. **Finish the composed caller gate.** Adapt the established independently scored browser/desktop workflow to caller v3. First prove the exact receipt, all-attempt accounting, intermediate-change stop, release, and cleanup path locally; then use only a valid, explicitly owned live allocation. Do not repeat consumed Calc or fixture runs.
3. **Run the matched efficiency comparison.** Freeze a current-main schedule for the simplest strong baseline, existing non-symbolic route, and compiled route. Match task/environment/model and score task effect independently. Include cold/warm, changed evidence, repair/recovery, latency, all provider attempts and token categories, release, and cleanup. Retain every arm and failure; decide using preregistered correctness and cost gates.
4. **Qualify recovery and repeatability.** Extend the two R41/R42 scoped successes with a prospectively frozen finite cohort covering source-action UNKNOWN, orphan recovery, late-input horizon, and a distinct eligible task effect. Report the complete denominator and censored/stopped attempts; do not turn a small fixture count into a reliability claim.
5. **Complete Research Preview and distribution gates.** On declared supported hosts, close the exact setup/doctor, retained audit, fresh no-retry live acceptance, and final audit requirements; verify that users can obtain and run the artifact. Keep dependency/runtime/model acquisition explicit and separately accounted.
6. **Reconcile the repository in bounded families.** Refresh complete Issue/PR membership, then map each family to its canonical question, current owner/state, evidence, successors, and next decision. Close or supersede only when the evidence supports that disposition; retain useful ideas and link their outcomes. In parallel, reconcile each dirty worktree/branch/output by path, owner, PR/Issue, and content hash before any move or deletion.

The order is dependency-aware, not a promise that every gate must block every other lane. A finite documentation or custody task may proceed when it directly enables the next experiment or safe integration. #59's current research priority remains controlling when choosing the next live research allocation.

## Evidence and decision rules

- Freeze the exact current-main source, hypothesis, comparator, sample/stopping rule, observable outcomes, exclusion rules, and cleanup plan before a formal run.
- Preserve raw output, conditions, hashes, failed setup, stops, and deviations. Do not rerun a consumed allocation or rewrite its historical interpretation.
- Distinguish synthetic/unit coverage, local integration, live mechanism evidence, task success, reliability, matched efficiency, preview acceptance, and public distribution.
- For local implementation checks, run normal and -O when relevant; report the actual environment and failures. Do not weaken acceptance gates to obtain a pass.
- Prefer existing mechanisms and evidence. Build a new mechanism only for a demonstrated residual that changes the next decision.
- Update Issues and PRs from verified outcomes. Counts, open state, a green check, or a merged archival packet alone do not determine scientific or product completion.

## Navigation and source of truth

- [Current goal](CURRENT_GOAL.md) - active project objective and newest bounded work.
- [Project state](PROJECT_STATE.md) - detailed gate dashboard and dated result handoff.
- [Roadmap](../ROADMAP.md) - product and research graduation gates, including #59's sequencing constraint.
- [Repository organization plan](REPOSITORY_ORGANIZATION_PLAN.md) - inventory, family triage, and custody cleanup.
- [Research method](RESEARCH_METHOD.md), [evidence map](EVIDENCE_MAP.md), and [research ledger](../RESEARCH.md) - how evidence is evaluated and where results live.
- [Worker work map](WORKER_WORK_MAP.md) and [quickstart](WORKER_QUICKSTART.md) - bounded tasks, collision checks, and execution practice.
- [Ideas and outcomes](IDEAS_AND_OUTCOMES.md) and [research issue index](RESEARCH_ISSUE_INDEX.md) - idea routing and disposition history.

When these summaries disagree with an experiment's frozen conditions or raw evidence, preserve the evidence and correct the summary. Never rewrite historical packets to make current status appear cleaner.
