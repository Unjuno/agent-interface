# Model coupling and evaluation validity agenda

Updated 2026-10-17 against `main` `1ece47014d05db898bf73afcd722a14524462e15`.
This is the next idea-family batch named by the [repository consolidation
status](../maintenance/consolidation-status-20261016.md). The issues below share
a concern with model behavior or model/interface comparisons, but they are
separate hypotheses and must keep separate evidence and decisions.

## 1. Opaque model behavior during route comparisons — #6001

- **Status:** Open; method evidence is scoped to authored synthetic fixtures.
- **Idea:** A bracketed, non-action canary deck may detect an in-deck behavioral
  shift behind a stable remote model alias during a route comparison. A clean
  deck means only `NO_SHIFT_DETECTED_IN_DECK`; it does not identify the model or
  prove that its behavior stayed fixed.
- **Evidence:** [PR #6088](https://github.com/Unjuno/agent-interface/pull/6088)
  passed its declared synthetic FCFS workload-interference fixture (3,840
  rows). Shared canary and equal-cost sham each added 6 seconds of modeled B
  queue wait; an isolated canary added none. [PR
  #6104](https://github.com/Unjuno/agent-interface/pull/6104) passed the
  synthetic shift-detection fixture (21,000 route outcomes and 420,000 probe
  attempts; independent audit errors 0; mutations rejected 9/9). [PR
  #6786](https://github.com/Unjuno/agent-interface/pull/6786) reproduced the
  frozen #6104 raw bytes under WSLc; it is a replay check, not an independent
  scientific replication. The allocation-01 and allocation-02 mount STOPs
  remain intact and are not results for the hypothesis.
- **Unresolved:** No provider/model call was made. Real endpoint drift,
  canary power/false-alarm behavior, provider queue/quota effects, and the
  causal validity of a route comparison remain untested. The shared-workload
  fixture is a reason to account for probe cost and interference, not to
  assume a canary is harmless.
- **Next decision:** For any future remote-model route comparison, first
  determine whether exact model/runtime pinning is available. If not, decide
  prospectively whether a privacy-safe, task-relevant canary and balanced
  route order are worth their workload cost. Any real endpoint evaluation
  needs its own budget, authorization, freeze and independent scoring; this
  agenda does not authorize one.

## 2. Model-by-interface interaction — #6035

- **Status:** Open; T0 method evidence is scoped to a finite synthetic fixture.
- **Idea:** Preserve same-model route comparisons as the primary estimate of
  an interface effect, then separately test whether that route effect changes
  across model capability profiles. Do not average away conflicting route
  effects or infer conditional route selection from one model.
- **Evidence:** A01 and A02 ended at pre-candidate source/main gates and remain
  STOP / NOT EVALUATED. [PR
  #6782](https://github.com/Unjuno/agent-interface/pull/6782) records A03's
  `PASS_METHOD_SCOPED`: its 64-row synthetic method distinguished an additive
  control (difference-in-differences 0), a planted crossover (−1.00), a hard
  safety failure and a no-common-contract HOLD. [PR
  #6968](https://github.com/Unjuno/agent-interface/pull/6968) preserves A01/A02
  STOP records. No real model or GUI was used.
- **Unresolved:** No two-model route contrast, common real task/effect cohort,
  model-specific cost comparison, or conditional route-selection policy has
  been evaluated.
- **Next decision:** Keep this behind the integrated efficiency milestone in
  [Issue #57](https://github.com/Unjuno/agent-interface/issues/57). Once a
  supported route and common task/effect contract exist, a separate prospective
  T1 can estimate each route contrast within at least two pinned models. If
  endpoint/tool contracts differ, report HOLD rather than a model-capability
  interaction.

## 3. Agreement-conditioned bounded continuation — #9004

- **Status:** Open. The frozen CPU-only T0 earned `PASS_METHOD_SCOPED` with
  `formal_pass=false` and `NO_INCREMENTAL_AGREEMENT_VALUE` on its synthetic
  trace family. The allocation ran once and is consumed; broader live-control,
  performance and product claims remain unverified.
- **Idea:** When a fast local policy and a delayed rich planner independently
  propose semantically equivalent actions for the same versioned state, a
  short continuation lease might reduce decision gaps while retaining
  independent safety, effect, freshness, revocation and release gates.
- **Boundary:** Agreement is not authority or proof of independent evidence.
  This differs from [#5352](https://github.com/Unjuno/agent-interface/issues/5352)
  (mode-switch chatter), [#4284](https://github.com/Unjuno/agent-interface/issues/4284)
  (specialist/backend promotion), and speculative-future proposals [#13](https://github.com/Unjuno/agent-interface/issues/13)
  / [#1074](https://github.com/Unjuno/agent-interface/issues/1074), which do
  not by themselves authorize effects during a planner delay. It also differs
  from #57's integrated route-economics question and #59's real-time control
  gate.
- **Evidence:** [PR #9009](https://github.com/Unjuno/agent-interface/pull/9009)
  retains 40 rows across ten synthetic cases and four arms; its independent
  raw-only auditor reconstructed all rows, and the mutation suite passed 5/5.
  Agreement-lease matched System-1-only; both acted in the same two cases with
  four total actions. All arms had a median synthetic inter-action gap of one
  tick, so the prospective 20% threshold was not met. No real latency, model,
  GUI, input, game or product outcome was measured.
- **Remaining question:** The Issue's narrower persistence hypothesis remains
  unverified beyond these frozen traces. Any further study must identify an
  agreement-specific benefit beyond System-1-only and use evidence suited to
  the claim; the consumed T0 is not rerun. The existing synthetic T0 proposal
  and its decision gates are preserved in the Issue and PR record rather than
  presented again as future work.
- **Decision boundary:** A method PASS can establish only the finite fixture's
  contract. A continuation-benefit claim requires separately authorized
  evidence with real timings and independent effects; the proposed 20% gap
  threshold is prospective, not an expected result.

## 4. Cue reliability under action-selected feedback — #8654

- **Status:** Open. C07 earned `PASS_METHOD_SCOPED` for auditing saved finite-
  design data; C06's original `FAIL_METHOD` remains unchanged.
- **Idea:** A policy's choices determine which action outcomes become observable.
  When unchosen outcomes are missing, factual feedback may not identify whether
  a visual cue's action/outcome relationship changed. Zero-support cells must
  remain `UNIDENTIFIABLE`, not be filled by counterfactual guesses.
- **Evidence:** Merged [PR #8671](https://github.com/Unjuno/agent-interface/pull/8671)
  preserves the read-only C07 audit of 15 C06 shards (197,376 histories): all
  six regime/policy groups had unit mass, the known-propensity expectation
  matched the finite all-action oracle, 768 greedy histories were
  unidentifiable, and 4/4 malformed-input controls were rejected. The auditor
  ran once and the candidate did not run in C07. This checks the stated finite
  design and saved-data audit; it does not show that diagnostic sampling
  improves an agent or that an agent adapts to cue reversal.
- **Unresolved:** C06's auditor mutation harness failed, and C07 does not repair
  or replace that disposition. Sequential interaction, carryover, empirical
  agent behavior, safe exploration, GUI effects, and product value remain
  unevaluated. Related [#8200](https://github.com/Unjuno/agent-interface/issues/8200)
  and [#8432](https://github.com/Unjuno/agent-interface/issues/8432) concern
  adaptation/recurrence under an available task-effect oracle; [#8640](https://github.com/Unjuno/agent-interface/issues/8640)
  concerns route-dependent outcome ascertainment. They are adjacent questions,
  not interchangeable evidence.
- **Next decision:** Decide in #8654 whether the remaining hypothesis warrants
  a separately frozen, independently audited test after resolving the C06
  method failure. This entry records the evidence and does not authorize a new
  allocation or live action.

## 5. Behavioral equivalence between benchmark variants — #8920

- **Status:** Open and unverified; no implementation or result is recorded.
- **Idea:** Matching required and forbidden endpoint effects may overlook
  differences in intermediate actions, hidden preconditions, or recovery paths.
  A finite labeled-transition audit could qualify variant equivalence under a
  declared abstraction while returning `UNKNOWN_MODEL_INCOMPLETE` when the
  transition model lacks coverage.
- **Boundary:** A certificate would establish equivalence only in the frozen
  abstract model. It would not establish equal visual difficulty, timing, agent
  performance, outcome-pooling validity, or transfer to a live application.
  Cosmetic renaming/layout mappings must be declared before scoring.
- **Next test:** The Issue proposes deterministic exhaustive T0 pairs with
  cosmetic changes, changed action availability, a forbidden intermediate
  state, altered recovery, hidden preconditions, and incomplete-model controls.
  Compare endpoint-only matching with an independent bisimulation oracle and
  require distinguishing traces for semantic differences. No result or
  allocation is claimed here.

## 6. Censoring-aware verifier ordering under workload drift — #8919

- **Status:** Open and unverified; proposed as an offline finite-method study.
- **Idea:** Under short-circuit verification, later predicate outcomes and
  costs are censored. A changing workload can make the most efficient order
  change, but estimating predicate selectivity only among cases that reach it
  can be biased. Compare a frozen order with an adaptive policy using only
  observed ordered outcomes and costs.
- **Existing evidence:** [#4258 / PR #4274](https://github.com/Unjuno/agent-interface/pull/4274)
  records a synthetic frozen-order cost reduction with exact three-valued
  semantics. [#4733 / PR #4735](https://github.com/Unjuno/agent-interface/pull/4735)
  maps a finite selectivity-drift crossover; the Issue retains a separate
  allocation-wide collision `HOLD`. Neither result establishes online
  adaptation. Preserve the #4733 collision record.
- **Decision boundary:** Mandatory predicates must all finish before `PASS`;
  `UNKNOWN` must not be upgraded. A method result cannot establish real
  verifier cost, workload prevalence, GUI benefit, or live safety.
- **Next test:** The Issue proposes a CPU-only deterministic drift fixture
  against the frozen #4258 order and an oracle, with independent enumeration of
  three-valued outcomes, censored suffixes, exploration cost, drift response,
  and no-shift overhead. It has no result or allocation here.

## 7. Calibration under corrupted verifier feedback — #8858

- **Status:** Open and unverified; no current repository feedback corruption is
  asserted.
- **Idea:** A sequential risk calibrator may be misled when its binary feedback
  bit is wrong, even when the event is observed rather than delayed or missing.
  Test whether a bounded method remains useful under directional/clustered
  label corruption, or whether excluding questionable labels and abstaining is
  the stronger baseline.
- **Boundary:** [#5315](https://github.com/Unjuno/agent-interface/issues/5315)
  covers assumption-conditioned verifier risk calibration, while
  [#7993](https://github.com/Unjuno/agent-interface/issues/7993) concerns
  delayed/censored labels. Integrity checks for modified raw artifacts do not
  test statistical robustness to an incorrect feedback label. No result may
  weaken evidence or authority gates.
- **Next test:** A finite CPU-only simulator must distinguish clean,
  directionally corrupted, clustered, and assumption-violating feedback, with
  an independent audit and simple label-exclusion/abstention baselines. This is
  a proposal only; no implementation or allocation is recorded.

## 8. Evidence-sufficient efficiency measurement — #8859

- **Status:** Open and unverified; no preference study or measured user
  preference is claimed.
- **Idea:** An efficiency measure should distinguish excess work from checks
  required to establish correctness, effect, and release. Fewer calls alone
  cannot earn efficiency credit when required evidence is missing.
- **Boundary:** This is a measurement layer for [#57](https://github.com/Unjuno/agent-interface/issues/57),
  not permission to remove observations, verifiers, release checks, or model
  boundaries. [#7705](https://github.com/Unjuno/agent-interface/issues/7705)
  studies elicitation methods, and [#7889](https://github.com/Unjuno/agent-interface/issues/7889)
  studies route-effect generalizability; neither provides preference validity
  for evidence-sufficient GUI traces.
- **Next test:** First assess whether existing successful traces can be
  independently classified as required versus excess work. Only if that
  feasibility gate passes should a small blinded pairwise-preference assay be
  considered. Objective outcomes such as tokens, wall time, and interruptions
  remain separately reported. No study or result is recorded here.

## 9. No-gold identifiability for GUI effect checkers — #8887

- **Status:** Open; A01 earned `PASS_COUNTEREXAMPLE_ONLY`, not a full method
  pass.
- **Idea:** Multiple checkers can agree perfectly while their accuracy remains
  unidentified if their outputs share a common evidence source. Agreement must
  not be presented as accuracy without justified source-independence or
  reference evidence.
- **Evidence:** Draft [PR #8893](https://github.com/Unjuno/agent-interface/pull/8893)
  records one eight-row counterexample: four checker columns have identical
  `00001111` outputs and 1.0 pairwise agreement in two hidden worlds with the
  same 0.5 truth prevalence, but finite-panel correctness is 1.0 versus 0.5.
  The candidate returned
  `UNIDENTIFIABLE_WITHOUT_INDEPENDENCE_EVIDENCE`; the independent auditor
  reconstructed both worlds and rejected 4/4 mutations. Candidate and auditor
  each ran once; retries were zero.
- **Boundary:** This single constructed control does not validate a latent-class
  estimator, quantify sampling uncertainty, or establish real GUI-checker
  accuracy. The broader factorial proposal in #8887 remains open; no estimate
  may prove an effect or grant action authority.
- **Next test:** Any continuation should identify which external source-lineage
  or independence assumptions can exclude the common-mode world, and when
  `UNIDENTIFIABLE` must remain the output. No new allocation is claimed here.

## 10. Revealed information-cost rationalizability — #8907

- **Status:** Open and unverified; no implementation, model call, or result is
  recorded.
- **Idea:** For a fixed model/version and controlled observation channel, test
  whether repeated query choices across downstream payoff schedules are
  rationalizable by one general information-acquisition cost on held-out
  decision problems. This is a measurement/diagnostic protocol, not a new
  query policy or a claim that the model has human-like preferences.
- **Relation:** #5306/#7934/#8879 study selecting observations or policies;
  #8623 studies epistemic-action benchmarking. #8907 instead evaluates the
  observed choices under incentive-crossed stakes. It is also distinct from
  [#8908](https://github.com/Unjuno/agent-interface/issues/8908), which tests
  time-consistency of a declared task-risk criterion, not query cost.
- **Prior work:** Caplin and Dean's [revealed-preference test for costly
  information acquisition](https://www.aeaweb.org/articles?id=10.1257%2Faer.20140117),
  Dean and Neligh's [experimental rational-inattention test](https://www.journals.uchicago.edu/doi/10.1086/725174),
  and Cook et al.'s [LLM revealed-choice analysis](https://www.federalreserve.gov/econres/feds/what-do-llms-want.htm)
  limit novelty claims. The proposed transfer is the GUI-agent query/action
  setting with actual runtime costs separately measured.
- **Next test:** Start with a small synthetic observation environment and
  scripted known-cost and inconsistent policies. Freeze payoff schedules,
  held-out tasks, test power, and negative controls (free perfect information,
  irrelevant/dominated cues, payoff transformations, and sequential variants)
  before any fixed-model call. Report metered tokens/latency separately from
  inferred behavioral costs. No external model/API budget or live GUI run is
  claimed here.

## 11. Budgeted discovery of failures in shallow-zero task cells — #8914

- **Status:** Open; two offline allocations are preserved as
  `HOLD_AUDITOR_METHOD_FAILURE`, with no scientific decision.
- **Idea:** Under a fixed repeat budget, can metadata and shallow outcomes
  prioritize frozen task cells with zero observed failures so held-out deeper
  trials discover more subsequent failures than uniform allocation? The target
  is discovery yield under the declared attempt distribution, not population
  risk estimation or certification that a cell is safe.
- **Proposed method:** Begin with an offline simulator. Compare uniform deep
  resampling, a simple preregistered ranker and a feature ranker trained only on
  shallow features/outcomes; reserve random sentinel trials to expose blind
  spots. Keep task families disjoint for training and evaluation, and admit a
  repeat only after an independent reset/state-hash check. Count reset failures
  as ineligible/held rather than as another sample.
- **Boundary:** #7889 asks about task/app breadth for route-effect
  generalizability, while #6001 tests temporal shifts in route comparisons.
  They remain separate estimands and controls here. A rank score is not a
  calibrated failure probability, and a shallow-zero or never-failed cell is
  not established safe. The proposal authorizes no live replay, GUI, model call
  or shared resource allocation.
- **Evidence:** [PR #9007](https://github.com/Unjuno/agent-interface/pull/9007)
  preserves A01 and A02, each of which ran the candidate/runner once and retained 61,800 attempt rows across
  103 synthetic worlds. Both independent audits exited at sentinel
  reconstruction before the scientific gates: A01 sampled from generation
  order while the auditor assumed sorted order; A02's runner reused its
  world-generation RNG state while the auditor restarted it. Both allocations
  are consumed; no mutation controls or retry were run. No candidate ranking
  benefit, null bound, or scientific pass/fail is established.
- **Next test:** Only a separately frozen allocation could continue this
  question. First qualify a deterministic sentinel contract and the independent
  auditor against constructed fixtures before any deep outcomes. This boundary
  applies to #8914 only and does not suspend other repository work.

## 12. Epistemic-action diagnostics and CLI custody — #8623/#8629/#8635

- **Status:** The three Issues remain open. Preserve #8623's historical result
  and later custody hold, #8629's consumed execution STOP, and #8635's
  construction-only repair separately.
- **Question:** Can independently authored held-out policies reveal which
  epistemic-action competencies aggregate task success conceals? #8629 adds
  independent task generation and raw-only auditing to the finite authored
  method proposed by #8623; it does not establish real-agent competence.
- **#8623 record:** A01's `PASS_METHOD_SCOPED` / `H_PASS_SCOPED` remains a
  historical report, but integration review found its formal run, raw candidate,
  raw audit and stderr streams absent from every PR commit. PR #8628 was
  returned to Draft with `HOLD_RESULT_CUSTODY`; the consumed allocation must
  not be rerun to recreate outputs.
- **#8629 record:** The one-shot A01 candidate exited 1 on an undefined
  `select_action`; the auditor then exited 1 parsing empty input. Candidate and
  auditor each ran once, retries were zero, no scientific rows were emitted,
  and the disposition is `HOLD_CANDIDATE_ENTRYPOINT_NAMEERROR`. Merged PR
  [#8634](https://github.com/Unjuno/agent-interface/pull/8634) preserves the
  exact failure; no retry or hypothesis inference follows.
- **#8635 record:** The successor construction packet fixed the CLI integration
  gap; actual candidate/auditor CLI tests passed and the construction suite
  passed 22/22 in normal and optimized Python. Merged PR
  [#8639](https://github.com/Unjuno/agent-interface/pull/8639) records only
  construction checks. Formal counts remain 0/0 and the packet is not frozen
  while shared WSLc ownership remains HOLD under #5085. Host execution or
  another container method is not a substitute for the registered gate.
- **Next decision:** Reconcile the shared runtime gate, then create a fresh
  current-main allocation with a complete freeze and independently authored
  task generator, policies, and auditor. This page does not authorize that
  execution or alter any prior allocation.


## 13. Weak-shadow-variable bounds for unresolved route outcomes — #8903

- **Status:** Open, unverified method-transfer proposal; no experiment, model
  call, implementation, or result is recorded.
- **Idea:** Test whether a frozen, route-blind prediction proxy for every
  prospectively assigned attempt can add defensible constraints to
  partial-identification bounds for unresolved route-success outcomes. The
  proxy is never treated as an outcome label; if its conditional restrictions,
  support, or leakage checks fail, retain the wider baseline bound or
  `UNIDENTIFIED`.
- **Relation:** #5590 supplies assumption-free bounds, while #8640/#8846 study
  route-dependent ascertainment and sensitivity to uncertain selection odds.
  #8903 asks whether weak-shadow-variable LP constraints add validated
  information beyond those baselines. It differs from #8887, which asks
  whether multiple fallible effect checkers can identify accuracy without
  gold labels.
- **Proposed test:** Freeze a binary route outcome, two assigned routes,
  covariates, ascertainment, proxy strata, LP restrictions, seeds, and an
  independent exhaustive oracle. Compare observed-outcome point estimates,
  #5590-style assumption-free bounds, #8846-style ascertainment-sensitivity
  bounds, and weak-shadow-variable bounds across informative and uninformative
  proxies, conditional dependence, route shift, outcome leakage, zero support,
  and outcome-dependent missingness. Report interval width, finite-world truth
  coverage, route-rank decisions, and false certification separately.
- **Boundary:** `PASS_METHOD_SCOPED` would apply only when the frozen proxy
  restrictions hold in the finite synthetic worlds and the independent audit
  validates coverage and corruption controls. It would not show that real GUI
  proxy assumptions hold or change any historical route ranking. No GUI,
  live model, participant, GPU, container, or external allocation is part of
  the proposal.

## 14. Independent-team replication of a frozen route effect — #8870

- **Status:** Open, unverified evaluation-method proposal; no external
  replication, participant study, model call, live GUI run, or repository
  effect is claimed.
- **Idea:** Test whether a separate team can execute one narrowly scoped,
  frozen route contrast on its own clean setup without author intervention,
  while preserving the same task/effect contract, hard-safety outcome, and a
  preregistered practical-equivalence band. Retain source and recipient
  outcomes separately; do not pool sites or choose only favorable source
  results.
- **Eligibility gate:** First establish one eligible claim with a complete
  task contract, recoverable raw packet, fixed route contrast, independent
  effect oracle, and a willing external team/site. Freeze source/dependency
  identities, model/runtime envelope where applicable, assignment/order,
  timeout/resource budget, all-attempt denominator, allowed deviations, and
  recipient-side source/readback checks. If any are missing, retain the
  corresponding HOLD; never rerun a consumed allocation to manufacture a
  replication target.
- **Relation:** #3033 checks artifact-packet recovery and audit replay; #12
  defines held-out task contracts; #5663 studies source-to-target transport;
  #7889 studies task/app sampling for route-effect generalizability; #8614
  addresses adaptive overfitting to reused cohorts. None alone executes the
  same frozen empirical claim through an independent operator/site.
- **Boundary:** `PASS_REPLICATION_SCOPED` would apply only to the selected
  claim, one external team, and its tested environment. A discrepancy does
  not identify its cause without further design; one successful site does
  not establish general reproducibility or cross-application validity. No
  external team, eligible claim, or replication result is recorded here.

## 15. Neutral context-length effects on fixed-model GUI decisions — #8856

- **Status:** Open, unverified transfer/evaluation proposal; no model or GUI
  result is recorded.
- **Idea:** Isolate length-only sensitivity by holding the exact decision
  evidence, its order and position, task, output schema, model/settings, and
  available actions fixed, then adding only preregistered neutral padding.
  A separately frozen equal-token semantic-distraction control must not be
  pooled with the length-only contrast.
- **Proposed test:** Use paired short and padded requests over exact-oracle
  GUI-like cases with a finite answer menu including `ABSTAIN`/`UNKNOWN`.
  Pin model/version/settings and serialization; verify actual provider token
  counts, position, and truncation; counterbalance order; retain all attempts;
  independently score wrong target/route proposals, unsupported claims,
  abstention, and schema validity. Downstream guards remain identical, and a
  blocked changed proposal is not counted as unchanged model behavior.
- **Relation:** #5329 tests whether compressed evidence preserves sufficient
  facts; #6241/#5947 test semantic contamination from other tasks or
  superseded values; #57 remains the integrated token/latency/correctness
  gate. #8856 asks whether neutral length alone changes model proposals when
  the evidence is held fixed.
- **Boundary:** A method pass validates only the manipulation and audit on
  the frozen cases. Behavioral support requires a predeclared paired effect
  threshold; otherwise report no effect at tested lengths or uncertainty.
  No consequence, visual-token effect, task completion, runtime adoption, or
  end-to-end efficiency claim follows without a separate #57-compatible
  evaluation.

## Priority and handoff

1. Continue #57's selected integrated path and resolve correctness/measurement
   blockers before spending remote-model budget on #6001 or #6035.
2. #8654's C07 audit is complete at method scope. Any follow-up must address
   C06's failed audit and make a distinct hypothesis decision; do not treat C07
   as evidence of agent adaptation or sampling benefit.
3. #9004's frozen T0 is now consumed and found `NO_INCREMENTAL_AGREEMENT_VALUE`
   on its synthetic traces; do not rerun that allocation. Its next stated
   discriminator is the common-mode-error comparison against an equally
   bounded System-1-only controller. Treat that as a distinct prospective
   allocation with its own current-main freeze, candidate output and independent
   audit; the existing result neither authorizes nor supplies that run.
4. #8920's finite transition-equivalence method is another untested proposal;
   keep its variant qualification separate from empirical difficulty or
   transfer claims.
5. #8919, #8858 and #8859 remain distinct evaluation questions: censored
   verifier ordering, corrupted-feedback calibration, and evidence-sufficient
   efficiency measurement. Their proposed work is offline and does not alter
   runtime policy.
6. #8887's A01 is a common-mode counterexample only. Keep the broader no-gold
   reliability method unvalidated until its assumptions and other regimes are
   audited.
7. #8914 remains an unverified allocation-method proposal. Its held-out
   discovery yield must stay separate from population-rate calibration and
   safety certification.
8. Return each result to its source Issue and this family map. Preserve all
   earlier STOP, FAIL, HOLD and PASS records; do not close an idea because its
   summary has been written here.
