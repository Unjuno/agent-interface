# Agent Interface project overview

**Snapshot:** origin/main at d4446aa82d182325a2a34ed89a085574c706f84c (2026-11-23). This is the short, project-wide orientation page. Detailed experiment records, failure history, and raw evidence remain in their existing locations.

## Purpose

Agent Interface aims to make computer control more effective while preserving the rich model's semantic understanding and strategy. Bounded local mechanisms may reduce repeated observation, waiting, and recovery when fresh evidence supports them. Correctness, authority, observable task effect, release, and finite recovery remain required; a faster but less reliable path is not a win.

The public product and research program are connected but distinct:

1. **A distributable runtime** must install and run on declared hosts, expose bounded inspectable control, preserve authority and release semantics, and pass a reproducible acceptance path.
2. **Research evidence** must show that the integrated route solves real tasks safely and improves end-to-end cost against a strong simple baseline. Unit tests, fake backends, synthetic composition, and package construction each prove only their recorded scope.
3. **Repository organization** must make work, evidence, ownership, and disposition discoverable without deleting viable ideas or closing Issues merely to reduce counts.

## Current state

At this snapshot, Issues [#53](https://github.com/Unjuno/agent-interface/issues/53), [#56](https://github.com/Unjuno/agent-interface/issues/56), [#57](https://github.com/Unjuno/agent-interface/issues/57), [#58](https://github.com/Unjuno/agent-interface/issues/58), and [#59](https://github.com/Unjuno/agent-interface/issues/59) remain open. [PR #10500](https://github.com/Unjuno/agent-interface/pull/10500) is merged into main. The Issue/PR counts below are explicitly dated baselines; this page does not claim that the full queue has been re-triaged.

| Area | What is established | What remains open |
|---|---|---|
| Integrated caller and compiled GUI route (#53, #56, #57) | [PR #10500](https://github.com/Unjuno/agent-interface/pull/10500) is merged. The caller-v3-to-compiled-GUI synthetic composition passes 2/2 focused cases and 132/132 related tests in normal and optimized Python. It accounts for two cold model attempts, makes two evidence-selected local transitions, and stops before a second input when intermediate evidence changes. | No live provider/app result through that composed route, no current-main matched economics, and no integrated repeated task/recovery estimate. The older three-arm result remains useful historical evidence but is not a current-main repetition. |
| Standard caller, effect, release, and recovery (#57) | R41 and R42 each recorded one public recovered-task success on a new HWND/PID generation after preserving the expired source action as UNKNOWN and replay-denied. Native expiry/recovery fixtures add scoped mechanics evidence. | Two fixture passes do not estimate reliability or establish same-window continuation, arbitrary-app, Calc, or MAP01 performance. Preserve the UNKNOWN boundary and all stopped/failed attempts. |
| Research Preview (#58) | A WSL package build and frozen-source retained audit passed; setup/launcher checks have partial coverage. | Supported-host readiness is incomplete. The current records do not establish the full doctor, fresh no-retry live run, final live audit, or browser-to-runtime control on the declared host. |
| Real-time control / MAP01 (#59) | The retained MAP01 work identifies a live threat-response gap; later controller and policy repairs have scoped evidence. The latest organization record says GZDoom/WAD were not found in the searched roots. | A current integrated threat-exposure test and a separately labelled MAP01 outcome are not established. Recheck supplied/preinstalled target and assets before any live run; do not install or download them as an incidental setup step. |
| Runtime distribution | Deterministic package construction and several startup/CLI contracts have passed on recorded hosts. | Publicly obtainable artifact plus declared-host live authority/input behavior and complete acceptance remain unverified. |
| Issue/PR and local artifact organization | Organization plans, evidence indices, historical inventories, and targeted family dispositions exist. | The latest exact full Issue/PR membership snapshot in the organization plan is r172 (1,640 open Issues / 405 open PRs); later work has merged, so those totals are a dated baseline. The semantic crosswalk is r160 and is not current whole-queue triage. Worktree/output custody still has unresolved historical entries. |

## Work order

1. **Protect the live research question.** Follow #59's requirement to resolve the real-time threat-response gap before spending a research block on presentation or broad packaging. Reuse retained MAP01 analysis and failures; first verify whether the intended executable and assets are already available. Freeze the current-main path and stop rule before any bounded live exposure.
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
