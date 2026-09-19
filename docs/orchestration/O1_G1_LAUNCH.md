# Orchestrator 1 — Generation 1 launch packet

## 1. Canonical snapshot and scope

CURRENT MAIN SHA: bc21199ac1e22ac34decc9fa1a73190e402480ee
CURRENT MAIN COMMIT MESSAGE: Measure retained MAP01 control tempo envelopes
MAIN COMMIT TIME: 2026-09-15 05:41:18 UTC / 14:41:18 JST
GOAL EPOCH: O1-20260915-CONTINUATION (administrative identifier; no goal reset inferred)
COORDINATION BRANCH: orchestrator/O1/G1-bc21199a
WORKER CODE/EVIDENCE BASE: bc21199ac1e22ac34decc9fa1a73190e402480ee

This coordination document is separate from main. Its containing commit must be pinned in the coordination Issue. Workers read this task authority separately; they do not use the coordination commit as their code/evidence baseline and do not merge it into their task branches.

The bootstrap SHA still equals main at the final pre-publication check. The repository and latest Issue #59 comments support a measurement-first real-time-control P0. No shared runtime implementation or new formal/live allocation is authorized here. Four tasks are AUTHORIZED_NOT_STARTED; this packet does not claim that four external ChatGPT sessions have been created or are running. No Worker result has yet been accepted.

The review used the GitHub connector for the current reference, relevant document sections, latest reports/preregistration, current implementation and Issue/PR state. It did not independently recompute the binary/raw-data audits. A local git clone was unavailable because the container could not resolve github.com; this does not prevent immutable-source review through GitHub. W1 and W5 own the bounded independent follow-through.

## 2. Evidence sources and changes to assumptions

Unless explicitly identified as mutable Issue state, every source below is read at the full WORKER CODE/EVIDENCE BASE above. Source filenames are repository-root relative.

Core: README.md; docs/CURRENT_GOAL.md r133; docs/LOCAL_RESEARCH_HANDOFF.md r133; docs/principles.md; RESEARCH.md; ROADMAP.md.

Current evidence:
- research/doom/MAP01_V38_V39_CONTROL_TEMPO_POSTHOC_V1.md
- research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json
- research/doom/analyze_map01_v38_v39_control_tempo_posthoc_v1.py
- research/doom/audit_map01_v38_v39_control_tempo_posthoc_v1.py
- research/doom/MAP01_V39_COAST_LIVENESS_LIVE_V1.md
- research/doom/map01_v39_coast_liveness_live_v1_prereg.json
- research/doom/results/map01-v39-coast-liveness-live-01/report.json
- research/doom/results/map01-v39-coast-liveness-live-01/audit.json
- research/doom/results/map01-v39-coast-liveness-live-01/audit-v2.json
- research/doom/MAP01_V38_INTEGRATED_LIVE_V1.md
- research/doom/map01_v38_integrated_live_v1_prereg.json
- research/doom/results/map01-v38-integrated-threat-live-01/report.json
- research/doom/MAP01_V32_FINAL_ADMISSION_LIVE_V1.md
- research/doom/results/map01-final-admission-v32-live-01/report.json
- research/doom/MAP01_ASTRA_ATTEMPT_V1.md
- research/doom/map01_astra_attempt_v1_prereg.json
- research/live_control/INTEGRATED_EFFICIENCY_LIVE_V1.md
- research/live_control/OPENTTD_EFFECT_MEMORY_ABLATION_V1.md

Mutable GitHub state inspected: Issue #59 is open, including correction comment 5675193176, v39 result comment 5675276842, and posthoc comment 5675340569. Issues #57/#58 remain sequencing context. Draft PR #1 and branch research/control-codec-track remain separate; they are not a Generation-1 dependency. The pre-launch branch listing contained main and that codec branch, but does not establish that no external/unreported sessions exist.

Corrections and refinements, not new discoveries after the bootstrap:
1. P0-A has an existing committed posthoc reconstruction. W1 must verify and extend its unresolved boundary, not build a competing reconstruction from scratch.
2. Issue #59's original v23/schema-v3 pointer is historical. The current formal/live path is v39/schema v6, session_map01_v12, Executor v12 and RunningActionGuard v3. ROADMAP.md explicitly defers to the updated goal and calls its older sections a backlog.
3. The corrected v38 explanation is an unauthored empty-coast zero-loss runtime guard after a rejected answer, not repeated overstrict model-authored policies. Preserve the superseded prose as historical attribution, not current truth.
4. V39's original formal audit remains failed on exact_frames. The separately versioned retained audit validates unchanged-image AIT reuse. Do not silently replace the original result with a pass.
5. Static source inspection finds timestamped key-down acknowledgements in input_owner_v10, but ordinary key-up returns no timestamped receipt. This is a specific telemetry lead, not proof that every retained backend log lacks a usable bound.
6. The v39 preregistration status string still mentions V38. Treat this as a metadata discrepancy for the audit matrix; it does not grant permission to edit the frozen preregistration or repeat the run.

## 3. Current evidence classification

PROVEN is reserved for explicitly bounded structural or checked-artifact claims, never broad runtime reliability. Existing audit pass statements below are repository-reported until independently reproduced.

- PROVEN, narrow static structure: select_cover_monitor chooses its no-policy mode only for empty commands, absent policy source iteration and absent authored validity. The inspected running guard requires matching program/intent identity and verified empty release evidence before early-release acceptance. This is not an exhaustive correctness proof.
- OBSERVED: integrated-efficiency-live-01 is RETAIN on one six-task sequence. Plain, ephemeral and persistent each completed 6/6 exact submissions. Persistent reduced model-visible work on that allocation; no broad GUI/general-speed conclusion follows.
- OBSERVED: v38 reports 27.489 s model wait, 11.418 s motor-capable program envelope, 16.022 s coast and 0.049 s no-program envelope; 2/6 completed answers and 1/6 model-plan admissions.
- OBSERVED: v39 reports 43.318 s model wait, 21.821 s motor-capable program envelope, 21.484 s coast and 0.013 s no-program envelope; 5/6 completed answers and 3/6 admissions. These categories measure program envelopes, not actual held-input occupancy.
- OBSERVED: two v39 post-rejection coast waits lost health from 85 to 73 and 73 to 68. Answer completion did not establish protection or useful control. The episodes/model actions differ, so v38/v39 differences are not an interface-causal comparison.
- OBSERVED: one v39 running-action revocation reached verified empty owned input 26.090 ms after typed event emission; terminal closure followed 52.961 ms later. This is one matched reaction event, not a latency distribution or a hard real-time bound.
- OBSERVED: v39 has nine accepted programs with matching empty-release terminals, 218 typed/exact observations and 217 PNGs because one exact observation reused prior PNG provenance. The original audit failed; retained audit v2 passes according to the repository.
- FAILED: the separately frozen Astra attempt died after 13 decisions / 149.911 s with one kill and no exit. Fixed cover expired before seven model returns. This does not identify the unique causal mechanism of death.
- FAILED: the original v39 audit's exact-frame counting condition. Its failure remains retained independently of the later audit.
- FAILED, scoped transfer: OpenTTD action-effect crop matched 1/2 engine-scored decisions versus current-only/full 2/2; DO_NOT_TRANSFER_CROP applies to that presentation/condition, not all memory.
- UNKNOWN: exact held-key durations; independently verified first useful MAP01 feedback; a counterfactual benefit from recovery; sustained useful renewal; matched human tempo; population reliability; cross-domain real-time efficacy; complete interrupted-turn token usage. MAP01 exit is false in the retained v38/v39 runs, not unknown.
- HYPOTHESIS: a separately authorized bounded recovery mechanism using fresh observable evidence could reduce harmful no-control exposure without weakening authority. It is not selected or validated by this packet.

Measurement conditions are retained single episodes, not new benchmarks. V39 requested gpt-5.6-luna/low, seed 990619, fixture map01-threat-contact-v2, six decisions, continuously advancing MAP01. The inspected session uses X11/ViZDoom, ASYNC_SPECTATOR, 35 tics/s and 640x480. Requested model identity must not be promoted to independently observed provider identity. Hardware, CPU clock, scheduler and logging-overhead evidence must be recovered or marked UNKNOWN; this review did not measure them.

## 4. Current P0 and why it precedes implementation

P0: determine whether authorized, useful control during frontier-model wait can be measured from retained evidence, then select the smallest general, falsifiable repair supported by that evidence.

The highest-value next decision is not 'which fallback should we implement?' It is 'which missing observation separates an input-free or merely active program from fresh authorized control with an independently useful effect?'

A better program-envelope number could conceal idle time, stale actuation or useless motion. Establishing measurement truth can therefore prevent an entire invalid live allocation. The current source/trace gaps also constrain every candidate, so this work has higher expected decision value than parallel speculative implementations. This priority judgment is an Orchestrator inference, not a numerically estimated information gain.

Initial H/T/D/C/U, explicitly NOT a frozen live preregistration:
- H: under matched task/fixture/model/permissions and predeclared wait exposure, an explicitly authorized bounded local mechanism reduces harmful no-control exposure while preserving freshness, scope, cancellation and verified release.
- T: first complete zero-live evidence reconstruction and trace-contract checks. W3 later freezes one finite matched candidate/control allocation, including allocation count, n_min, schedule, model settings, observation permissions, source closure, retry rule and stopping rule. Those numeric choices are UNSET now and block live activation.
- D: PASS requires the predeclared useful-effect/exposure endpoint and every correctness/retention gate. FAIL includes an authority/release violation or failure of a valid exposed endpoint. UNCERTAIN covers missing telemetry, unexposed trigger, inadequate independent scoring, or incomparable conditions. Do not manufacture a success threshold from observed outcomes.
- C: extra input causes harm; no-input is the correct policy; model-wait or trajectory differences explain the apparent gain; hidden scorer leakage helps the candidate; logging overhead changes exposure; a program ends without useful effect.
- U: clock-domain alignment, sample censoring, key release visibility, source/evidence identity, scorer lag, scheduling, provider variance and hardware/logging overhead. Unknown uncertainties stay unknown; a combined uncertainty or coverage factor requires justified assumptions, not a decorative number.

If useful effect cannot yet be identified, select measurement-only instrumentation as the next candidate. Do not force a recovery implementation merely to keep W4 occupied.

## 5. Dependency graph and activation gates

W1 retained-evidence delta -------\
W2 measurement contract ----------+--> O1 evidence/contract gate --> O1 frozen question
W5 initial correctness matrix ----/                                  |
W6 cross-domain assessment --> generality challenge -----------------+
                                                                    |
                                                              W3 frozen design
                                                                    |
                                                  O1 exact mechanism + write lease
                                                                    |
                                                       W4 sole implementation
                                                                    |
                                                    W5 independent candidate audit
                                                                    |
                                              O1 exact source/allocation freeze
                                                                    |
                                            W3 sole formal-live allocation owner
                                                                    |
                                             O1 RETAIN/REPAIR/REJECT/BLOCKED
                                                                    |
                                                    recompute P0-P3; do not drift

W6's complete output need not block W1/W2/W5 work. It is required before describing a mechanism as general or authorizing cross-domain promotion. W3 starts only after accepted W1/W2/W5 inputs and an O1-frozen question. W4 starts only after a justified exact mechanism, sufficiently fixed experiment design and an exact file allowlist. W5's executable audit extension is a separate successor task, not implicit authority in its startup task. A later W3 live task receives its own immutable BASE COMMIT and separate formal experiment lease.

The separately labelled MAP01 attempt comes only after relevant corrected-control live evidence. W7's second-domain integrated evaluation remains dependency-bound; its planning/implementation is not part of W6's startup work. W8 remains idle unless a new important independent bounded task appears.

## 6. Ownership and shared-source quarantine

Task namespaces below are reservations, not wildcard write grants. Only the exact files in each envelope may change.

| Owner | Namespace / authority | Initial status |
|---|---|---|
| O1 | docs/orchestration/O1_G1_LAUNCH.md; coordination Issue body; integration decisions | active coordinator |
| W1 | research/orchestration/o1-g1/w1/; four exact files below | authorized, not acknowledged |
| W2 | research/orchestration/o1-g1/w2/; three exact files below | authorized, not acknowledged |
| W5 | research/orchestration/o1-g1/w5/; three exact files below | authorized, not acknowledged |
| W6 | research/orchestration/o1-g1/w6/; two exact files below | authorized, not acknowledged |
| W3 | no write or live lease yet | WAIT |
| W4 | no shared-runtime lease yet | WAIT |
| W7 | no write or experiment lease | WAIT / dependency-bound |
| W8 | none | IDLE |

Workers read but do not modify README.md, CHANGELOG.md, RESEARCH.md, ROADMAP.md, docs/CURRENT_GOAL.md, docs/LOCAL_RESEARCH_HANDOFF.md, docs/principles.md, this launch packet, prior preregistrations, retained result trees, fixtures or baseline sources. Only O1 may later grant a new exact lease. During any W4 shared lease, O1 also avoids concurrent edits to that component.

Inspected current path and quarantine includes:
- research/doom/map01_overlap_controller_v39.py
- research/doom/session_map01_v12.py
- research/doom/doom_typed_release_backend_v1.py and doom_typed_coast_backend_v1.py
- research/doom/doom_typed_observation_v1.py, doom_hud_signal_v3.py, doom_action_snapshot_v1.py, doom_action_validity_contract_v1.py
- research/doom/map01_cover_policy_schema_v6.json and map01_motor_responder_v10.txt
- research/live_control/executor_v12.py and inherited executor dependencies
- research/live_control/input_owner_v10.py
- research/live_control/lease.py and lease_release/lease_cause dependencies
- research/live_control/running_action_guard_v1.py, running_action_guard_v2.py, running_action_guard_v3.py
- research/live_control/final_action_admission_v2.py, action_validity_admission_v1.py, observable_signal_guard_v2.py
- research/live_control/persistent_planner_adapter_v2.py, codex_app_server_client_v2.py, coast_backend_v1.py and inherited session/backend code.

The v39 preregistration's direct source map is an input to W5, not an assumption of complete transitive closure. The inspected controller contains machine-specific Windows Node/CLI paths; no replacement executable, endpoint, DISPLAY, WAD or model may be silently substituted.

## 7. Initial P0-P3 roadmap

Costs and information gain below are qualitative scheduling judgments, not measured estimates.

### P0 — Measurement truth and correctness boundary
QUESTION: What can retained evidence establish about fresh authorized useful control during model wait?
CURRENT EVIDENCE: Existing r133 reconstruction; v39 liveness/revocation; unresolved physical occupancy and useful-feedback endpoints.
REMAINING UNCERTAINTY: Identifiability, exact provenance, release/clock coverage and transferable semantics.
DEPENDENCY: Frozen baseline only; independent startup tasks may proceed in parallel.
EXPECTED INFORMATION GAIN: Highest immediate decision value; may prevent a scientifically invalid candidate/allocation.
IMPLEMENTATION COST: Low-to-moderate offline review/reconstruction; no runtime changes.
CONFLICT RISK: Low under four disjoint exact allowlists.
EXPERIMENT COST: Zero new model/GUI/live allocations.
ASSIGNED ROLE: W1/W2/W5/W6, synthesized by O1.
STATUS: Four tasks authorized, no execution acknowledged.

### P1 — Conditional next executable path
QUESTION: Is the smallest justified next intervention telemetry-only, bounded recovery, guard/abort/switch, or no new code?
CURRENT EVIDENCE: Coast damage and stale-action rejections motivate a question, not a selected policy.
REMAINING UNCERTAINTY: Mechanism, useful-effect oracle, thresholds and an identifiable matched comparison.
DEPENDENCY: Accepted P0 outputs; O1 question; W3 design; exact W4 lease; W5 audit.
EXPECTED INFORMATION GAIN: High only once endpoints are identifiable.
IMPLEMENTATION COST: Unknown until the bounded mechanism is selected; one implementation path.
CONFLICT RISK: High in shared runtime, controlled by a single writer.
EXPERIMENT COST: Zero until freeze, then one finite formal allocation with a new ID.
ASSIGNED ROLE: W3 steward; W4 sole implementer; W5 independent auditor; O1 final gate.
STATUS: WAIT; neither code nor live authority granted.

### P2 — Dependency-bound demonstration and second-domain replication
QUESTION: Does the corrected mechanism transfer and support a separately labelled advancing MAP01 attempt?
CURRENT EVIDENCE: Desktop persistence retained on one sequence; MAP01 incomplete; OpenTTD crop transfer rejected in one condition.
REMAINING UNCERTAINTY: Generality, sustained control, new-domain effect predicates and matched end-to-end benefit.
DEPENDENCY: Relevant P1 evidence and new explicit allocation/design; second-domain work must not displace unresolved P0.
EXPECTED INFORMATION GAIN: High after the local mechanism is identifiable; low as an immediate distraction.
IMPLEMENTATION COST: Moderate/unknown until domain and predicate are selected.
CONFLICT RISK: Moderate; separate adapter/test files preferred.
EXPERIMENT COST: New separately labelled allocations, never inherited from G1 authority.
ASSIGNED ROLE: W7 later for integrated evaluation; W3 later for MAP01 stewardship.
STATUS: WAIT.

### P3 — Research backlog and convergence
QUESTION: Which packaging, portability, compact-IR or broader interface work becomes necessary after the evidence gates?
CURRENT EVIDENCE: Research Preview and desktop demo exist; codec draft remains separate.
REMAINING UNCERTAINTY: Product support envelope, native portability and general economic benefit.
DEPENDENCY: P0 resolution or a demonstrated concrete research/safety/reproduction blocker.
EXPECTED INFORMATION GAIN: Lower than the current observed control gap.
IMPLEMENTATION COST: Potentially broad; intentionally unallocated.
CONFLICT RISK: High if broad refactors or codec merge disturb the baseline.
EXPERIMENT COST: Not allocated.
ASSIGNED ROLE: None; W8 stays idle.
STATUS: BACKLOG, not silently cancelled.

FROZEN / REJECTED: all consumed allocations remain immutable; v39's original failed audit remains; the tested OpenTTD crop presentation is not transferred; unchanged hero retries, expired-policy rebasing, competing runtime candidates and unrelated codec/packaging work are not authorized.

## 8. Common Worker execution and return protocol

These requirements are incorporated into every envelope below.

Verify the full BASE COMMIT and create exactly the stated worker branch from it. Do not pull/rebase onto moving main, cherry-pick another Worker's output, or substitute a missing asset. Read this coordination packet at its separately pinned commit. Check that the assigned output paths do not contain pre-existing work at BASE; a collision requires O1 review, not an improvised rename.

Before analysis, post one STARTED acknowledgement in the coordination Issue that pins this packet, including TASK ID, ROLE, BASE COMMIT, BRANCH, exact OWNED FILES and environment. An unacknowledged assignment is not RUNNING. These tasks permit no model/endpoint preflight, game/GUI session, X11 input, hidden-state controller access or formal allocation. Static reading and safe deterministic replay/tests are allowed only where the individual envelope permits them.

Inspect audit/test entrypoints before running them. Several retained audits may write results in place; never execute an overwriting default against the retained tree. Use a read-only source copy and temporary outputs or an explicitly redirected safe path. Uncommitted scratch is disposable and must not be cited as canonical evidence. Relevant outputs must fit the exact allowlist and be committed.

No Worker consumes another Worker's unpublished or newly committed result during this startup task. They share only BASE evidence and this packet. O1 later binds accepted cross-Worker inputs by exact HEAD SHA in a successor task; this avoids moving cross-task contracts and preserves independent audit authorship.

Commit and push bounded useful work; do not merge yourself. Return in the coordination Issue:
TASK ID:
RESULT CLASS: exactly one recommended RETAIN / REPAIR / REJECT / BLOCKED
BASE COMMIT:
HEAD COMMIT:
BRANCH:
FILES CHANGED:
TESTS: command/environment/outcome, or explicitly NOT RUN
EVIDENCE: immutable path/hash and event/record identifiers
FAILED / UNKNOWN:
SUGGESTED SUCCESSOR: proposal only

A push failure means completion is not canonical. BLOCKED before changes may have no HEAD beyond BASE. A proposed REPAIR must name the exact defect, causal evidence, bounded repair, required files and new test. Stop after this return; do not execute successors. Silence does not authorize automatic task reassignment or lease expansion. O1 resolves stale/replacement sessions using a new task identity and, where necessary, new paths.

## 9. Exact startup envelope — W1

TASK ID: O1-G1-W1-EVIDENCE-01
ROLE: W1 — Retained Evidence & Failure Reconstruction
BASE COMMIT: bc21199ac1e22ac34decc9fa1a73190e402480ee
BRANCH: worker/W1/O1-G1-W1-EVIDENCE-01
OBJECTIVE: Determine the incremental truth obtainable beyond the existing r133 reconstruction, including which held-input/useful-effect questions are fundamentally unobserved.
WHY NOW: Existing envelope metrics and coast damage do not establish useful authorized control or the cause of Astra's death. Reimplementing the published analysis without a new discriminator wastes work.
OWNED FILES:
- research/orchestration/o1-g1/w1/evidence.md
- research/orchestration/o1-g1/w1/claims.json
- research/orchestration/o1-g1/w1/provenance.json
- research/orchestration/o1-g1/w1/reconstruct.py
DO NOT TOUCH: Every other tracked file; all original reports, raw evidence, preregistrations and runtime; W2 definitions and W5 audit artifacts.
INPUT EVIDENCE: The source list in section 2, especially the existing posthoc analyzer/audit/analysis.json, Astra first failure, all v38/v39 decisions and releases, v32 expiry-race records, and relevant input-owner/backend logging. Discover linked retained raw paths from these manifests, never from a mutable latest directory.
WORK TO PERFORM: Reproduce the published analysis only as a validation step, with no retained-tree writes. Bind source/output bytes by hash. Inspect all selected Astra/v38/v39 decision windows and the v32 expiry race; map answer, program, policy, lease, key admission/release, typed evidence, damage/resource and scorer events. Determine exact values versus interval bounds versus UNKNOWN. Resolve the corrected v38 attribution and separate v39's original failed audit from audit v2. Investigate whether key-up/hold-end/backend records actually close the occupancy gap; do not fill it with requested duration or terminal time. List the smallest additional telemetry that would distinguish competing explanations. Keep requested and independently observed model identity separate.
EXPERIMENTAL CONSTRAINTS: Common protocol; zero new model/GUI/live calls; offline pure reconstruction only. The optional reconstruct.py is confined to reading retained bytes and producing allowlisted or temporary derived output. No runtime or instrumentation implementation. No v38/v39 causal-speed or health-protection claim.
REQUIRED OUTPUT: A PROVEN/OBSERVED/HYPOTHESIS/FAILED/UNKNOWN claim matrix; event/hash-backed evidence; coverage/uncertainty and clock notes; minimal telemetry gaps; a primary result recommendation and at most one justified immediate successor proposal. Equations, when needed, must have complete variable meanings, SI units, types, ranges/assumptions and a unit check.
STOP CONDITION: Stop after every selected episode/window and core claim is reconciled, bounded or explicitly UNKNOWN and the output is pushed. If essential assets cannot be retrieved/verified, retain the exact missing paths and bounded partial analysis; do not generate replacement evidence or expand the study.
LIVE EXPERIMENT AUTHORITY: NONE.
SHARED WRITE LEASE: NONE.

## 10. Exact startup envelope — W2

TASK ID: O1-G1-W2-MEASUREMENT-01
ROLE: W2 — Useful-Control Measurement Contract
BASE COMMIT: bc21199ac1e22ac34decc9fa1a73190e402480ee
BRANCH: worker/W2/O1-G1-W2-MEASUREMENT-01
OBJECTIVE: Specify a general, implementable measurement contract that distinguishes program existence, valid authority, backend-confirmed input, useful effect and independent semantic feedback.
WHY NOW: A controller improvement cannot be falsified using program-envelope occupancy or pixel change alone.
OWNED FILES:
- research/orchestration/o1-g1/w2/measurement-contract.md
- research/orchestration/o1-g1/w2/event-schema.json
- research/orchestration/o1-g1/w2/trace-cases.json
DO NOT TOUCH: Every other tracked file; no executable implementation, runtime, existing schema/preregistration, retained trace, W1 reconstruction or W5 audit.
INPUT EVIDENCE: r133 report and analysis; current v39 preregistration and controller; input_owner_v10.py; executor_v12.py; lease.py and release lineage; running_action_guard_v3.py; integrated desktop and OpenTTD effect reports listed above. Use only BASE evidence, not pending W1 output.
WORK TO PERFORM: Define a dictionary and event identity contract for model wait, program lifetime, policy-source freshness, live lease, input-active, authorized-idle, unauthored coast, no-program, environment/resource changes, useful effect, independent first useful feedback, revoke/cancel, physical release and terminal completion. Represent overlapping dimensions rather than forcing lease/program/input states into an invalid single partition. Specify interval unions, censoring, missing boundaries, duplicate/out-of-order events, clock domains and permissible bounds. Separate X11/server-observed owned key/button state from device hardware state and application consumption. Include at least six non-executable trace examples: authorized idle, unauthorized input, coast during damage, early release before terminal, overlapping holds and missing/out-of-order boundaries. Show that no-input can be correct and held input can be useless. Prevent scorer-only privileged state from entering controller observations.
EXPERIMENTAL CONSTRAINTS: Common protocol; documentation/JSON schema/examples only; zero new model/GUI/live calls. Draft operational definitions, not a frozen efficacy threshold or candidate implementation. Do not choose a recovery maneuver or grant authority.
REQUIRED OUTPUT: Versioned draft contract, machine-readable event schema and trace examples with expected classifications/bounds/UNKNOWN outcomes; required telemetry versus already observable fields; measurement-overhead and clock assumptions; explicit variable table/units/types/ranges and a dimensional check wherever formulas are used. Mark underdetermined useful-effect endpoints UNRESOLVED.
STOP CONDITION: Stop after all required distinctions and six examples are covered, consistency is checked, remaining identifiability gaps are explicit, and the three files are pushed. An unidentifiable useful-effect endpoint is a valid result, not permission to invent one.
LIVE EXPERIMENT AUTHORITY: NONE.
SHARED WRITE LEASE: NONE.

## 11. Exact startup envelope — W5

TASK ID: O1-G1-W5-AUDIT-01
ROLE: W5 — Independent Authority & Regression Audit
BASE COMMIT: bc21199ac1e22ac34decc9fa1a73190e402480ee
BRANCH: worker/W5/O1-G1-W5-AUDIT-01
OBJECTIVE: Build an independent requirement-to-test matrix and source/provenance closure for the current path before a candidate writer can define its own success gate.
WHY NOW: Apparent liveness can be produced by weakened freshness, rebased budgets, incomplete release evidence or an over-permissive audit.
OWNED FILES:
- research/orchestration/o1-g1/w5/audit-matrix.md
- research/orchestration/o1-g1/w5/source-closure.json
- research/orchestration/o1-g1/w5/check-results.json
DO NOT TOUCH: Every other tracked file; no runtime, tests, old audit, preregistration or result-tree modifications. Do not repair the v39 failed audit or its metadata in place.
INPUT EVIDENCE: Current v39 source/preregistration, session_map01_v12, inherited executor/lease/backend/input-owner path, running guards v1-v3, final/action-validity admission and observable-signal guard, existing offline tests, v32 expiry race, v38 report and v39 original/retained audits.
WORK TO PERFORM: Trace actual imports and runtime sources.json against preregistered hashes, separating direct manifest coverage from transitive dependencies and environmental binaries. Map requirements to existing test IDs and retained events: stale rejection, source-age expiry, immutable loss budget, focus/surface/epoch binding, scope, action/policy validity, running revocation, cancel/terminal race, matching program/intent identity, early and terminal empty release, no input after rejection, no authority expansion, and useful effect versus completion. Include the legal case where a planner is already terminal but its answer remains ineligible. Flag missing/duplicate releases, wrong-intent events and unverified physical state. Review the ordinary key-up receipt gap, scheduler-dependent owner behavior, hardcoded host paths and the v39 preregistration status discrepancy. Safe existing pure tests may be run only after checking that they cannot start a GUI/model or modify frozen evidence; otherwise record NOT RUN with the exact dependency.
EXPERIMENTAL CONSTRAINTS: Common protocol; zero new model/GUI/live calls; no new executable audit/test implementation in this first task. Do not import the entire live runner merely to collect tests. Preserve independent authorship; consume no W1/W2 draft as accepted truth.
REQUIRED OUTPUT: Requirement/test/evidence/verdict matrix with PASS/FAIL/UNKNOWN/NOT RUN distinctions, transitive source closure with exact hashes or missing status, environment/commands/check outcomes and a minimal future executable-audit task proposal. Existing repository pass reports and freshly executed checks must be separately labelled.
STOP CONDITION: Stop when every listed requirement maps to a concrete existing check or an explicit gap, the bounded safe checks are recorded and files are pushed. A safety or provenance defect causes a bounded finding, not a unilateral repair or scope expansion.
LIVE EXPERIMENT AUTHORITY: NONE.
SHARED WRITE LEASE: NONE.

## 12. Exact startup envelope — W6

TASK ID: O1-G1-W6-TRANSFER-01
ROLE: W6 — Cross-Domain Control Semantics
BASE COMMIT: bc21199ac1e22ac34decc9fa1a73190e402480ee
BRANCH: worker/W6/O1-G1-W6-TRANSFER-01
OBJECTIVE: Distinguish general Agent Interface semantics from domain-specific policies and identify counterexamples to proposed useful-control abstractions.
WHY NOW: MAP01 exposes the gap but must not silently define the whole interface. OpenTTD already supplies a retained negative transfer result.
OWNED FILES:
- research/orchestration/o1-g1/w6/transfer-matrix.md
- research/orchestration/o1-g1/w6/assessment.md
DO NOT TOUCH: Every other tracked file; no runtime, benchmark/planner, fixtures, scorer, launch work or second-domain live experiment.
INPUT EVIDENCE: docs/principles.md; r133 and v39 reports; INTEGRATED_EFFICIENCY_LIVE_V1.md; OPENTTD_EFFECT_MEMORY_ABLATION_V1.md and their linked retained evidence at BASE. First task uses retained evidence only, not a new literature sweep or model study.
WORK TO PERFORM: Map observation freshness, intent/lease lifetime, local guard, cancellation/release, no-input behavior, effect verification and terminal state across MAP01, Chromium desktop and OpenTTD. For each proposed general semantic primitive, identify a retained supporting example, a counterexample or explicit missing evidence, a domain adapter obligation and what would falsify transfer. Keep academic disciplines distinct from benchmark domains: use control/real-time systems, distributed systems and experimental science/causal inference. Explicitly test the counterexamples 'waiting is correct' and 'more actuation is harmful/useless'. Explain why health floors, firing and retreat are domain policies rather than universal interface primitives. Do not infer broad memory failure from the scoped crop rejection.
EXPERIMENTAL CONSTRAINTS: Common protocol; zero new model/GUI/live calls; no W7 evaluation design beyond one bounded successor sketch. No full benchmark suite, taxonomy expansion, implementation or selection of the P0 mechanism.
REQUIRED OUTPUT: Three-domain evidence/semantics matrix; general-versus-adapter classification; counterexamples; missing transfer evidence; one recommendation to retain, restrict or reject an abstraction and at most one minimal successor discriminating test sketch.
STOP CONDITION: Stop when all listed primitives have three-domain cells with evidence or UNKNOWN and a falsification criterion, then push the two files. Do not activate W7 or execute the proposed test.
LIVE EXPERIMENT AUTHORITY: NONE.
SHARED WRITE LEASE: NONE.

## 13. No-rerun ledger and integration rules

No previously consumed formal allocation ID may be reused anywhere in the repository. In particular preserve the first outcomes for:
- map01-final-admission-v32-live-01
- map01-schema-v6-preflight-01
- map01-v38-integrated-threat-live-01
- map01-v39-coast-liveness-live-01, including both original failed audit and separate audit-v2
- the Astra allocation named in map01_astra_attempt_v1_prereg.json (do not confuse its allocation ID with its retained directory/video filename)
- integrated-efficiency-live-01
- openttd-effect-memory-ablation-01
- all earlier consumed MAP01 compiler/schema/threat allocations and failed desktop allocations, even if not individually enumerated here.

Read-only recomputation of retained evidence is allowed within the task envelope and is not a fresh live retry. It must not overwrite an old analysis/audit. A live repair requires a new code version, preregistration, immutable source closure and allocation ID. A new ID alone never authorizes an unchanged hero retry.

O1 reviews returned work in dependency-aware order: W1 evidence and W5 safety findings first as they arrive, W2 contract reconciliation next, W6 generality challenge before mechanism promotion. Disjoint outputs may be accepted in any arrival order, but acceptance does not silently update another running task's BASE or contract. Integrate only an exact pushed HEAD after verifying its BASE ancestry, complete changed-file list, ownership, evidence and test claims. Freeze the reviewed SHA; a later push requires a new review. Resolve documentation contradictions in O1 synthesis, not by having Workers edit one another's output.

Each accepted result receives one primary RETAIN/REPAIR/REJECT/BLOCKED classification. A REPAIR names an exact defect, evidence, bounded change, files and new test; 'try again with more changes' is not an acceptable successor. Main movement affects only newly issued tasks. No automatic successor or formal experiment lease exists.

Goal reset: preserve retained evidence and stopping rules of already-frozen allocations; stop creating old-goal successors; record the new explicit goal epoch and canonical state; revoke irrelevant pending task authority without destroying completed evidence; recompute P0-P3 and issue a new generation.

## 14. Compact Orchestrator replacement handoff

CURRENT MAIN SHA: bc21199ac1e22ac34decc9fa1a73190e402480ee
GOAL EPOCH: O1-20260915-CONTINUATION; no new user goal reset
CURRENT GOAL: General agent-native interface with slow semantic planning and fast fresh, scoped, auditable local control
CURRENT P0: Measurement truth for useful control during model latency; no candidate preselected
WHY P0: Existing coast/program metrics cannot identify useful actuation/effect; unresolved Issue #59 remains the sequencing constraint
PROVEN: Only bounded static structure and repository-reported retained checks; see section 3
FAILED: Astra exit attempt; original v39 exact-frame audit; scoped OpenTTD crop transfer
UNKNOWN: True held-input occupancy, first independent useful MAP01 feedback, causal benefit, reliability, human tempo, cross-domain control efficacy, complete interrupted usage
ACTIVE WORKERS: 0 acknowledged/running by this packet; W1/W2/W5/W6 authorized to start
COMPLETED WORK: O1 repository-state review and this bounded launch structure; no Worker completion
PENDING RESULTS: STARTED acknowledgements and four bounded deliverables
FILE OWNERSHIP: Exact allowlists in sections 9-12; global/shared files read-only
BLOCKED WORK: W3 design activation; W4 implementation; all live allocations until prerequisites pass
READY NEXT: W1/W2/W5/W6 startup tasks only
FROZEN / REJECTED: Prior allocations/failed audits; scoped crop transfer; no expired-policy rebasing or unrelated codec merge
EXPERIMENTS THAT MUST NOT BE RERUN: Section 13; all consumed formal IDs
IMPORTANT DEPENDENCIES: W1/W2/W5 acceptance then frozen question; W6 generality check; W3 design; sole W4 path; independent W5 audit; one W3 allocation
OPEN WRITE LEASES: Four disjoint output reservations; no shared-runtime lease
CURRENT FORMAL EXPERIMENT LEASE: NONE issued by O1; external unreported process state is not established by this packet
NEXT ORCHESTRATOR ACTION: Validate the first Worker STARTED receipt against this packet's full BASE COMMIT, branch and exact allowlist before marking that task RUNNING.
