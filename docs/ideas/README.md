# Idea History

This directory is the compact history of ideas raised in Agent Interface.

The latest complete paginated metadata snapshot is [open Issues r68](../maintenance/open-issues-20261019-r68.csv) and [open PRs r68](../maintenance/open-prs-20261019-r68.csv), captured at 2026-10-19 04:15:55 UTC against main `20a17d8b99879f7804a679d2dc2927d5e6b4cb3a` with 1,673 open Issues and 491 open PRs. These inventories establish membership and PR metadata, not semantic classification or current ownership. The [r52 coverage audit](../maintenance/idea-index-coverage-20261019-r52.md) shows 489 open Issues without a primary row in the historical research selection; all 489 remain routed through the completed B01–B20 receipts, which are discovery aids rather than semantic classifications. The r15/r50/r51/r52 snapshots remain immutable history. The older r53 CSV paths are not row-level inventories; see the r57 recheck for the file-integrity correction.

Use this directory to connect ideas to existing evidence, dependencies, priorities and executable experiments. GitHub Issues remain the discussion and execution surface. Preserve each distinct hypothesis and its outcomes here before deciding its Issue state. The [repository consolidation plan](../REPOSITORY_CONSOLIDATION.md#2026-10-19-全体整理の実行計画--アイデアを保存して作業面を収束) permits an idea-only Issue to be individually closed as catalogued/deferred after the canonical idea entry and return link are recorded; active experiments, unresolved user goals, evidence/ownership gaps and integration work remain open until resolved or explicitly superseded. Issue closure never means the underlying idea succeeded.

## What belongs here

For each idea, retain:

- **Idea** — the proposal or hypothesis in one short statement.
- **Source** — the originating GitHub Issue(s) or retained research record.
- **Outcome** — what was learned, implemented, rejected, superseded, or left unresolved.
- **Status** — one of:
  - **adopted**
  - **rejected**
  - **superseded**
  - **on hold**
  - **unverified**
  - **inconclusive**

Closed Issues remain valid provenance and should not be omitted merely because they are closed.

## Entry format

```markdown
## <Idea title>

- **Status:** <status>
- **Source:** #123, #456
- **Idea:** <one-paragraph summary>
- **Outcome:** <brief result; link to detailed evidence when useful>
```

## Index

- [Reactive motor primitives and compiled symbolic GUI interfaces](reactive-macro-symbolic-interface.md) — keeps #6's broad local-continuation menu distinct from #56's model-authored symbolic interface and connects their scoped construction results to the open, provenance-failed composition package #7616.

- [Current open-work inventory r51 (2026-10-19)](../maintenance/repository-inventory-20261019-r51.md) — complete paginated metadata: 1,675 open Issues and 503 open PRs; sorted ID hashes match r50. Membership metadata is not semantic triage or ownership proof.
- [r51 issue-index coverage audit and disjoint discovery queue](../maintenance/idea-index-coverage-20261019-r51.md) — 491 missing-primary-row Issues partitioned into 20 fixed batches; batches are navigation/assignment boundaries, not semantic families.
- [Issue discovery batch receipts B01/B02](../maintenance/issue-discovery-b01-20261019.md) · [B02](../maintenance/issue-discovery-b02-20261019.md) — document which ideas are already routed, what parent summaries were added, and the specific review limits; no Issue is closed by routing.
- [Issue discovery batch B03](../maintenance/issue-discovery-b03-20261019.md) — routes MAP01, lifecycle, and watcher items; records merged PR references and the unpublished #197 v3 custody limit without promoting the parent issue.
- [Research and idea Issue index](../RESEARCH_ISSUE_INDEX.md) — broad discovery index with a historical state snapshot and newer addenda; check its freshness note and live Issue/evidence before disposition. This ledger is the compact hypothesis/outcome map, not a complete mirror of every research-index row.
- [Conflict-aware evidence ledger](conflict-aware-evidence-ledger.md) — reconciles #5305's merged finite T0, held-out STOP, later policy counterexample, raw-custody gap, and unverified provenance refinements without closing the Issue or rerunning T0.
- [Evidence-admission family](evidence-admission-family.md) — links #5314 dependency-aware quorum, #5305 conflict representation, and #5339 trust/coverage while preserving each finite result, audit failure, assumption, and unresolved boundary.
- [Historical open Issue/PR inventory r8 (2026-10-18)](../maintenance/repository-inventory-20261018-r8.md) — preserved metadata snapshot, not the current baseline; see r12 above.
- [Historical open Issue/PR inventory r7](../maintenance/repository-inventory-20261018-r7.md) — preserved earlier snapshot against pre-#9029 main.

- [MAP01 live threat-guard evidence family](map01-live-guard-evidence-family.md) — indexes eight #59 allocation packet groups through A15 and separates result/custody limits. #8678/#8701 tracked files are preserved, #8749/#8782/#8790/#8810 result packets are merged, and #8818 adds A15's manifest without raw contents. A10/#8759 and A14/#8800 remain open for distinct raw-custody gaps. No allocation was rerun.

- [Open Issue inventory refresh (2026-10-17)](../maintenance/open-issues-inventory-20261017.md) — refreshes the paginated open-Issue metadata snapshot to 1,677, records its three-ID delta from r3, and states that inventory is not full semantic triage.

- [Model integration, matched economics and evaluation ideas](model-economics-agenda.md) — #57/#3311 execution, #5827 endpoint sensitivity, #6227 requalification cost and #8859 evidence-sufficient effort remain distinct. Includes current/legacy accounting adoption checks and original-result custody gaps; no live performance claim.

- [Safety control, interruption, evidence and recovery](safety-control-agenda.md) — distinct hypotheses in #2/#10/#14/#15/#16/#17, dependencies and executed public-path Fake X blocking characterization. These parent ideas remain open.

- [Research Issue index addendum (2026-10-17)](../RESEARCH_ISSUE_INDEX_20261017_ADDENDUM.md) — captures 146 currently open research-labelled Issues missing from the historical 2026-10-02 selected index, with literal outcome markers and heuristic predecessor refs; it is discovery metadata, not semantic audit.

- [Open issue citation audit (2026-10-17)](open-issue-citation-audit-20261017.md) — restores direct links and concise proposal summaries for 61 open Issues (49 in the original bounded comparison plus 12 found in a follow-up live recheck); source Issues remain authoritative for evidence, status, and execution decisions.

- [Chance-bounded task progress under stochastic delays](chance-bounded-task-progress.md) — keeps #8596 A01 invalidation separate from A02's finite exact-rational result and the unresolved MDP/calibration question.

- [Split-control value of information](split-control-voi.md) — separates #8638 A01's missing raw-output custody from A02's scoped ranking-reversal result.

- [Route/task-mix hysteresis under feedback](route-task-hysteresis.md) — separates #8648 C01's WSLc initialization STOP from C02's finite coupled-model result.

- [Reset-aware ordered event coverage for GUI histories](ordered-context-event-coverage.md) — connects #7452 to merged successor #8399/#8402, distinguishes A01's unequal-universe comparison from A02's equal-denominator result, and preserves the separate #8401 protocol STOP.

- [Action-conditioned incorrect-belief exposure](action-conditioned-incorrect-belief-exposure.md) — records #7986's synthetic measure without claiming live authority or safety.

- [Bandwidth inheritance for blocked verifiers](bandwidth-inheritance-blocked-verifiers.md) — links #7944/#7979 and their finite offline BWI result.

- [Slack reclamation for sporadic control deadlines](slack-stealing-sporadic-deadlines.md) — consolidates #7778's zero-overhead and dispatch-sensitivity synthetic results while preserving priority-only as the stronger full-matrix baseline.

- [WSL Container API session reuse](wslc-api-session-reuse.md) — distinguishes #8518’s fresh-container API-session reuse proposal from #6693’s Docker-versus-WSLc comparison; preserves the no-run and ownership gates.

- [Same-host WSLc iteration cost](wslc-iteration-cost.md) — records #6693’s unrun Docker-versus-WSLc comparison, its shared-runtime start gate, and the non-comparative #6352 portability result.

- [Post-GA WSL filesystem placement](post-ga-wsl-filesystem-placement.md) — preserves #7970's scoped WSLc-lane readiness boundary and no-run status.

- [Decision value over likelihood ambiguity](decision-value-likelihood-ambiguity.md) — records #7955's finite likelihood-set result and limits.

- [Outcome-conditioned GUI reversibility](outcome-conditioned-gui-reversibility.md) — preserves #7949's STOP/raw and peer-review coverage concerns.

- [Post-success artifact changeability](post-success-artifact-changeability.md) — consolidates #6610's scoped synthetic result and #8578's duplicate disposition; correction-cycle refinements stay with #6610.

- [Decision-value observation stopping](decision-value-observation-stopping.md) — separates #7934's historical A01/A02 results from its later noncanonical launcher STOP.

- [V39/V15 retained audit provenance](v39-v15-retained-audit-provenance.md) — keeps #7921/#7933 audit failures and #8192 manifest issue separate.

- [WSLc client ownership readiness](wslc-client-ownership-readiness.md) — records #7924's scoped ownership/current-main HOLD without a repository-wide stop.

- [Source-time expiry for negative evidence](source-time-expiry-negative-evidence.md) — preserves #8466's finite logical-time result without implying query completeness.

- [Specification-diverse oracle challenges](specification-diverse-oracle-challenges.md) — records #8088's scoped no-incremental-value result and predecessor HOLDs.

- [Confusion-adaptive GUI practice](confusion-adaptive-gui-practice.md) — preserves #8084's scoped synthetic gate results and low-dispersion false activations.

- [Blocked versus interleaved GUI practice](blocked-interleaved-gui-practice.md) — indexes #8080's synthetic method readiness without inferring human transfer.

- [Relation-first idea retrieval](relation-first-idea-retrieval.md) — records #8073's consumed search-surface STOP and unevaluated hypothesis.

- [History-conditioned repair](history-conditioned-repair.md) — indexes #8068's canonical finite result and trace-eligibility HOLD.

- [Unknown job-class fail-closed handling](unknown-job-class-fail-closed.md) — records #8061's scoped boundary result without a scheduler claim.

- [Internal versus environmental GUI memory](internal-vs-environmental-gui-memory.md) — preserves #8057's finite method result and safety-floor failures.

- [Repeated-cohort IPCW coverage](repeated-cohort-ipcw-coverage.md) — records #8049 A03 and keeps the predecessor FAIL/STOP separate.

- [Delayed GUI-procedure retention](delayed-gui-procedure-retention.md) — indexes #8032's no-participant power-sensitivity packet.

- [Calibrated recovery deadlines](calibrated-recovery-deadlines.md) — records #8024's synthetic result and fixed-timeout equivalence.

- [Recording-salience reactivity](recording-salience-reactivity.md) — indexes #8022's consent-bounded, unrun human-study proposal.

- [Epoch-bound transform chain](epoch-bound-transform-chain.md) — distinguishes #8185's non-conclusive A01 packages from #8201's synthetic exact-oracle successor.

- [Screen-reader handback continuity](screen-reader-handback-continuity.md) — records #8166's AT-state observability hold without inferring state from focus.

- [WSLc threat-profiled eligibility](wslc-threat-profiled-eligibility.md) — preserves #8150's blind-review disagreement without certifying a runtime as a sandbox.

- [Persistent counterparty adaptation](persistent-counterparty-adaptation.md) — records #8135's construction-only state and missing isolated runtime preflight.

- [Checkpoint clairvoyant diagnostic repair](checkpoint-clairvoyant-diagnostic-repair.md) — records #8283's retained-data repair without revising #7466's scientific result.

- [Held-modifier chord composition](held-modifier-chord-composition.md) — preserves #8252's remaining paced-text prefix gap after the initial merged refusal fix.

- [Typed-observation NaN elapsed](typed-observation-nan-elapsed.md) — records #8249's confirmed malformed-metadata gap and unmerged patch.

- [Empty-event-index fast path](empty-event-index-fast-path.md) — records #8244's merged change and scoped hosted regression evidence.

- [State-conditioned observation omission](state-conditioned-observation-omission.md) — indexes #8397's distinct A01 protocol deviation and A02 finite trace result.

- [Carbon-window byte-bound replay](carbon-window-bytebound-replay.md) — preserves #8386 A05's exact-byte replay and the unresolved A04 metadata mismatch.

- [Matched-context fixture integrity](matched-context-fixture-integrity.md) — carries #8313/#8341/#8353's successive auditor gates without promoting the invalid A02 gate.

- [Caps Lock query-to-XTEST race](capslock-query-to-xtest-race.md) — records #8328's protocol-only status and absence of a formal run.

- [Feedback factorial and retained-raw audits](feedback-factorial-and-retained-raw-audits.md) — preserves #8319/#8327's failure, review correction, and pending audit-only successor.

- [Journal/state reconciliation](journal-state-reconciliation.md) — distinguishes #8300's original result, duplicate custody record, and separate byte-bound replay.

- [Retrieval practice for takeover readiness](retrieval-practice-takeover-readiness.md) — records #8498's synthetic instrument PASS without inferring human or live-user benefit.

- [Global queue synchronization](global-queue-synchronization.md) — preserves #8494's image-preflight boundary and zero formal invocations.

- [Trace reduction under regime drift](trace-reduction-regime-drift.md) — records #8493's finite temporal-drift method result and open evidence PR.

- [Scoped GUI plan infeasibility](scoped-gui-plan-infeasibility.md) — records #8473's symbolic method result without claiming GUI applicability.

- [Switched-control dwell stability](switched-control-dwell-stability.md) — preserves #8471's finite results and separate trajectory-evidence eligibility limit.

- [Compositional visual-control stability](compositional-visual-control-stability.md) — records #8470's eight-case gain-screen result and limits.

- [Disturbance-order correlation](disturbance-order-correlation.md) — records #8434's synthetic equal-exposure schedule result.

- [System-carbon rebound](system-carbon-rebound.md) — records #8421's synthetic accounting sign reversal without an empirical emissions claim.

- [Episodic-memory consolidation schedule](episodic-memory-consolidation-schedule.md) — keeps #8406's unrun A19 separate from open model-free threshold calibration.

- [PSI-triggered work shedding](psi-triggered-work-shedding.md) — preserves #8488's corrected deadline-semantics HOLD and records that no container/T1 pressure test ran.

- [Context-return renewal](context-return-renewal.md) — preserves #8432's distinct A01 method failure and A02 raw-custody STOP without claiming behavioral evidence.

- [WSLc smoke evidence audits](wslc-smoke-evidence-audits.md) — records #8446/#8455's separate audit-only failures and distinguishes the host-only prep branch.

- [Observation load versus cue information](observation-load-cue-information.md) — preserves #8665's mixed synthetic factorial result without transferring it to GUI/OS load or user tempo.

- [Policy-dependent ascertainment](policy-dependent-ascertainment.md) — keeps #8640's consumed disk STOP and distinct finite A02 PASS separate; no live-route bias claim.

- [Epistemic-action CLI construction](epistemic-action-cli-construction.md) — records #8635's construction repair while retaining the dated shared-runtime gate and zero formal invocations.

- [Evidence readiness and epistemic action](evidence-readiness-epistemic-action.md) — preserves #8623's reported method result and distinct raw-receipt custody HOLD; no rerun to recreate missing receipts.

- [Common-cause degradation contracts](common-cause-degradation-contracts.md) — carries #8610's protocol-arm correction and #8622's corrected A02 result/custody boundary without pooling the allocations.

- [Safe observation-predicate synthesis](safe-observation-predicate-synthesis.md) — indexes #8562's unverified allowlisted-grammar proposal and dated no-run status without turning it into a repository-wide gate.

- [Decision regret over stale-feedback windows](decision-regret-stale-feedback.md) — records #8528's synthetic-method PASS separately from any causal, GUI, or deployed-safety claim.

- [Safety-aware verifier backpressure](safety-aware-verifier-backpressure.md) — keeps #5372’s endogenous-demand counterexample, route-expansion result, and authoritative-cap boundary separate; preserves the unverified workload-origin transfer question.

- [Persistent-sojourn gating](persistent-sojourn-gating.md) — records canonical open #6650’s `FAIL_HYPOTHESIS`, its controller-law audit limit, the #6673 serialization-only correction, and #8891’s non-independent estimator refinement.

- [Safety control, interruption, evidence and recovery](safety-control-agenda.md) — distinct hypotheses in #2/#10/#14/#15/#16/#17, calibrated soft-signal recovery deadlines (#8024), protective-control diagnosability (#8909), and incremental stratified negative-claim maintenance (#8917), with dependencies, the executed public-path Fake X blocking characterization, and scoped A01 evidence. These source Issues remain open.

- [Spatial-block position generalization](spatial-block-position-generalization.md) — preserves #6590’s method PASS, geometry/support holds, T1 audit failure, and corrected `H_FAIL_SCOPED` outcome as separate evidence.

- [Visual representation, addressing and feedback](visual-interface.md) — #4's broad interface thesis, optional grids (#3), visual addresses/feedback contracts (#5), adaptive view-set selection (#7), and composite observations (#8), with [the research execution agenda](visual-interface-agenda.md). The record keeps selection (#7) separate from packing (#8), reuses #1946/#1968 integrity findings, and does not treat #2031's schema-confounded score as valid localization accuracy. It also separates finite-sample observation-channel dominance (#8911) from #6678's known-kernel comparison, and keeps image-space Jacobian adaptation (#7765) distinct from #5's safety/recovery contract. Original bodies and provenance are preserved; read current Issues before disposition.

- [Assumption-gated evidence acquisition](evidence-acquisition-policy-selection.md) — tests when greedy observation choice is justified and when bounded lookahead is worth its cost (#8879), without granting runtime authority.

- [Counterfactual responsibility for negative queries](negative-query-counterfactual-responsibility.md) — preserves #8624's finite method result and duplicate-allocation boundary while keeping query completeness and live visual applicability separate.

- [Query-private evidence-location lookup](query-private-evidence-location.md) — preserves #8000's no-eligible-workload HOLD and separate WSL-container STOP; no PIR or privacy result is claimed.

- [Effect-indexed semantic deoptimization](effect-indexed-semantic-deoptimization.md) — records #8040's finite cursor-reconstruction PASS while keeping external GUI effects, runtime resumption, and its Draft evidence PR unresolved.

- [Failure-episode unitization and linkage uncertainty](failure-episode-unitization-sensitivity.md) — records #7857's synthetic segmentation-sensitivity result and T1 HOLD, plus #8004's distinct joint boundary/linkage result and its Draft evidence PR.

- [Client energy per verified effect](client-energy-per-verified-effect.md) — keeps #7728's macOS sensor HOLD separate from Windows counter-only observations; no matched-route energy result is claimed.

- [Agreement-conditioned bounded continuation](agreement-conditioned-continuation.md) — records #9004's consumed synthetic T0 (`PASS_METHOD_SCOPED`, `NO_INCREMENTAL_AGREEMENT_VALUE`) without inferring live control or timing benefit.

- [Benchmark-variant behavioral equivalence](benchmark-variant-equivalence.md) — indexes #8920's unverified finite-method proposal; no cohort, transfer, or equal-difficulty result is claimed.

- [Censoring-aware verifier ordering](censoring-aware-verifier-ordering.md) — connects #8919's unverified online-learning proposal to the distinct static-order and drift-boundary evidence in #4258/#4733, preserving their limits and audit outcomes.

- [Incremental nonmonotone claim maintenance](incremental-nonmonotone-claim-maintenance.md) — indexes #8917's unverified DRed-versus-rebuild proposal, with explicit completeness/epoch prerequisites and no GUI claim.

- [Producer-side dispatch pacing](producer-side-dispatch-pacing.md) — records #8916's unverified simulator-only comparison against immediate and reactive queue-aware policies.

- [Delegation-membership identifiability](delegation-membership-identifiability.md) — indexes #8915's unverified identical-trace discriminator without conflating membership, event causality, and actor attribution.

- [Trace-mined metamorphic relations](trace-mined-metamorphic-relations.md) — indexes #8904's unverified method-transfer proposal against the manually declared #5513 baseline; no universal relation or runtime authority is claimed.

- [Weak-shadow bounds for unresolved route outcomes](weak-shadow-route-outcome-bounds.md) — indexes #8903's unverified proposal against #5590/#8640/#8846; a proxy is only an auxiliary restriction, never a missing-outcome label.

- [Recoverable-pause transition accounting](recoverable-pause-transition-accounting.md) — indexes #8902's within-task multi-state evaluation proposal and distinguishes it from #8068's history-conditioned repair estimand.

- [Functional search diversity in diagnosis](functional-search-diversity-diagnosis.md) — indexes #8901's unverified fixed-budget hypothesis-coverage comparison; disagreement and diversity alone are not evidence of better diagnosis.

- [Post-crash effect-reconciliation bootstrap](post-crash-effect-reconciliation-bootstrap.md) — indexes #8900's finite root-reachability proposal while preserving UNKNOWN and keeping action/retry authority revoked.

- [Bounded-error diagnosability](bounded-error-diagnosability.md) — indexes #8898's unverified robustness successor to noiseless #8894; no real error rate or new locating-array construction is claimed.

- [Telemetry-channel-aware allocation](telemetry-channel-aware-allocation.md) — indexes #8897's synthetic resource-information question and separates it from observation-value, observer-cost, and WSL-accounting work.

- [Invariant-confluence coordination overlap](invariant-confluence-coordination-overlap.md) — records #8889's substantial overlap with #5547/#5563 and preserves the narrow unresolved comparison without duplicating an allocation.

- [No-gold effect-checker identifiability](no-gold-effect-checker-identifiability.md) — records #8887's unverified method and merged #8893's narrower agreement/accuracy counterexample without promoting it to full method validation.

- [Recurrent-disturbance recovery envelope](recurrent-disturbance-recovery-envelope.md) — indexes #8872's unverified disturbance-magnitude × spacing proposal, preserves #5776's failed early-warning result, and requires consolidation if #5372 or #5776 already exposes the same endpoint.

- [Independent-team route replication](independent-team-route-replication.md) — indexes #8870's unverified one-site replication proposal, distinguishing independent execution from evidence-packet audit, task sampling, and source-to-target transport.

- [Budgeted hidden-failure discovery](budgeted-hidden-failure-discovery.md) — preserves #8914 A01/A02 as distinct consumed auditor-method HOLDs; neither supports a scientific conclusion and neither may be retried.

- [Split-view evidence detection](split-view-evidence-detection.md) — indexes #8912's unverified witness-gossip discriminator, keeping fork detection separate from truth, capture completeness, and authority.

- [Observation-channel kernel uncertainty](observation-channel-kernel-uncertainty.md) — indexes #8911's unverified confidence-set successor to #6678 without revising prior synthetic or browser-fixture results.

- [Diagnosability under protective control](protective-control-diagnosability.md) — preserves #8909's scoped A01 mask/restoration result, construction mismatch, assumed sentinel, and unmerged Draft evidence status.

- [Time-consistent task risk](time-consistent-task-risk.md) — indexes #8908's unverified finite decision-method proposal, preserving hard constraints and distinguishing information-driven policy changes from same-node preference reversal.

- [Revealed information-cost rationalizability](revealed-information-cost-rationalizability.md) — indexes #8907's fixed-model query-choice diagnostic, keeping operational API costs separate from inferred behavioral cost and preserving its unverified status.

- [Evidence coordination and delegation observability](evidence-coordination-agenda.md) — keeps split-view detection (#8912) and delegation-membership identifiability (#8915) unverified, while preserving #8587's separate finite multi-source trace-reconciliation result and its GUI/source-completeness limits.

- [Claim preservation under runtime loss](claim-preservation.md) — distinguishes fixity, interpretability, auditability, re-execution, and reproduction for #8905; a host-only raw-auditor follow-up is recorded, while the proposed three-package offline test remains unverified.

- [Task risk semantics and sequential decisions](risk-semantics-agenda.md) — separates #26's bounded task posture and proposed trajectory-risk composition from #8908's unverified within-task time-consistency question.

- [Recoverable-pause trajectory measurement](recoverable-pause-trajectory-measurement.md) — records #8902's unverified within-task state-accounting proposal separately from terminal-outcome, mission-survival, and recovery-mechanism questions.

- [Model coupling and evaluation validity](model-coupling-and-evaluation-agenda.md) — includes #9's learned-local-control question and keeps opaque model-behavior stability (#6001), model-by-interface interaction (#6035), revealed information-cost rationalizability (#8907), epistemic-action diagnostics and custody (#8623/#8629/#8635), action-selected cue-reliability feedback (#8654), benchmark-variant transition equivalence (#8920), censored verifier ordering (#8919), budgeted failure discovery (#8914), corrupted-feedback calibration (#8858), evidence-sufficient efficiency measurement (#8859), no-gold effect-checker identifiability (#8887), agreement-conditioned bounded continuation (#9004), and weak-shadow-variable bounds for unresolved route outcomes (#8903), independent-team replication of a frozen route effect (#8870), and neutral context-length effects on GUI decisions (#8856) distinct while connecting their scoped evidence and next tests.

- [Benchmark-wave comparability](benchmark-wave-comparability.md) — records #8885's unverified anchor-invariance-gated comparison between non-identical task waves and its refusal conditions; same-task pairing remains preferred.

- [Human evaluation validity](human-evaluation-validity.md) — preserves the prediction-labeled takeover question (#5935), consent-bounded recording salience (#8022), learning-transfer and user-relative benefit questions (#6600, #6593), their synthetic method limits, and the gates for any future participant study.

- [Control dynamics and route recovery](control-dynamics-agenda.md) — keeps route-by-disturbance evaluation (#6604), source-supported path-class switching (#6586), reset-qualified trial-to-trial residual learning (#8661), and phase-dependent controllability under interface delays (#8668) distinct, preserving the synthetic outcomes and their limits.

- [Runtime reliability under uncertainty](runtime-reliability-agenda.md) — separates liveness suspicion (#5531), timed resource deadlocks (#5410), verifier-cascade capacity (#5375), and hidden-state belief contracts (#5368), preserving distinct finite-method results, allocation failures, and unresolved integration boundaries.

- [Observation-fiber updateability and allocation custody](observation-fiber-updateability-custody.md) — separates #6775’s canonical nine-row result from #6774’s separately disclosed 12-row duplicate and unresolved executor custody.

- [Observation load, dispatch pacing, and feedback cascades](observation-load-cascade-agenda.md) — separates #8665's scoped factorial result, #8888's implementation/audit STOP, and #8916's unverified producer-pacing proposal.

- [Freshness-gated observation hedging](freshness-gated-observation-hedging.md) — keeps #7383's WSLc and host CPU simulator results distinct and preserves the untested real-capture critical-path gate.

- [Post-crash effect reconciliation bootstrap](crash-reconciliation-bootstrap.md) — records #8900's unverified question about independently rooted, read-only evidence paths for `UNKNOWN_RECONCILE`, with task and retry authority held revoked until classification.

- [Timing privacy and control utility](timing-privacy-control-utility.md) — connects #6201's scoped synthetic metadata-leakage result to #8899's unverified controller-utility/privacy frontier, keeping safety clocks and noncritical timing treatment distinct.

- [Progressive and lossy evidence descriptions](progressive-lossy-evidence.md) — separates #8865's nested-versus-independent budget summaries from #8875's subset utility under loss, reordering, and interruption, including the receiver-side-information and semantic-coding boundaries.

- [Skill-conditioned terminal-event memory](skill-conditioned-terminal-event-memory.md) — records #8886's unverified fixed-context progress-memory contrast and its provenance/effect boundaries.

- [Provenance-bound object memory](provenance-bound-object-memory.md) — records #7167's deterministic authority-preservation T0 while keeping model compliance and #8618's action-admission question untested and separate.

- [Telemetry-aware resource allocation](telemetry-aware-resource-allocation.md) — links #8897's unverified noisy-telemetry scheduling proposal to #8488's corrected, deadline-semantics HOLD without implying host-pressure evidence or a WSL policy.

- [GUI macro transfer and translation validation](gui-macro-transfer-validation.md) — separates #8890's appearance/function relation test, #7827's finite A05 result, and #8869's unverified external-interleaving successor.

- [Semantic dependency audit](semantic-dependency-audit.md) — links #8883's bounded black-box discovery proposal with #4233's retained audit-control HOLD and later read-only corrections, without converting them into a PASS.

- [Guard-evidence applicability envelope](guard-evidence-applicability-envelope.md) — records #8631 A01/A02 failures and construction-only evidence separately from the scoped A03 method result in merged PR #8633.

- [Spatial coordinate risk](spatial-coordinate-risk.md) — distinguishes #8881's probability-mass propagation proposal from #6684's finite relational-bound result and existing point-revalidation work.

- [Assistive-technology co-activity](assistive-technology-coactivity.md) — separates #8880's concurrent human/AT non-interference proposal from #5922's presentation-configuration study and its invalidated T0.

- [Validity-preserving trace reduction](validity-preserving-trace-reduction.md) — distinguishes #8878's regenerated valid executions from #5666's frozen-trace delta debugging and preserves its no-replayable-failure HOLD.

- [Trace-derived metamorphic relations](trace-derived-metamorphic-relations.md) — records #8904's unverified trace-mining proposal and its separation from relation declaration and trace reduction.

- [Constrained interaction-fault diagnosis](constrained-fault-diagnosis.md) — separates #5330's detection result, #8901's unverified early-search portfolio, #8894's fault-set identifiability, #8895's adaptive-versus-fixed cost frontier, and #8898's corruption robustness.

- [Invariant-confluence coordination boundary](invariant-confluence-coordination-boundary.md) — consolidates #5547's scoped finite evidence and #8889's corrected overlap without duplicating its broad allocation.

- [Joint reserve and model-lifetime](joint-reserve-model-lifetime.md) — keeps #8630's failed weak-signal gate, #6580's bounded T0c pass plus remaining HOLD, and #8873's post-result full-tree policy audit distinct.

- [Task-conditioned degraded envelopes](task-conditioned-degraded-envelope.md) — records #8586 A01/A02 finite-model results separately, with the live capability, runtime, and integration boundaries.

- [Partial GUI target correspondence](partial-target-correspondence.md) — updates #8675's scoped synthetic T0 result and records #8868's separate unmatched-node successor without treating either as live identity or authority.

- [Privacy-preserving failure discovery integrity](privacy-discovery-integrity.md) — records #6549's scoped 24-row feasibility result and #8877's separate unverified coalition-integrity successor, without claiming DP or fleet deployment.

- [Cleanup identity audit and evidence custody](cleanup-identity-audit.md) — preserves #8681's duplicate-ID failure, the single merged #8771 implementation boundary, and the distinct evidence still carried by overlapping #8687/#8838 PRs.

- [Versioned semantic degradation](versioned-semantic-degradation.md) — separates #8609's independent-failure finite result from #8610's protocol-arm mismatch and #8622's corrected but custody-held common-cause result.

- [Belief-space recovery and predicate synthesis](belief-recovery-and-predicate-synthesis.md) — preserves #8527's pre-run STOP, #8553's scoped result plus audit gap, and #8562's unverified successor under an ownership HOLD.

- [Early-warning signal identifiability](service-early-warning-identifiability.md) — separates #5776's recovery-rate method failure and artifact-integrity hold from #8525's preflight STOP and #8872's unverified disturbance-spacing successor.

- [Controller portfolio and evidence-planning cost](controller-portfolio-and-evidence-planning-cost.md) — keeps #8864's portfolio-cardinality comparison distinct from #8851's topology-guided evidence-action shortlist and exact fallback.

- [Predicate-aware GUI history reduction](predicate-aware-gui-history-reduction.md) — separates #8592's scoped lifecycle DPOR result, #8613's phantom-membership method result, and #8663's combined finite result with an audit-count deviation.

- [Controlled development feedback](controlled-development-feedback.md) — records #8072 A01 audit rejection and the distinct A02 scoped result, separated from #8319/#8327 factorial and audit work.

- [Controlled feedback and raw-artifact bypass](controlled-feedback-artifact-bypass.md) — preserves #8581 A01/A02 audit failures and A03's audited no-incremental-bypass result while keeping all evidence PRs unmerged and distinct.
