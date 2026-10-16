# Model coupling and evaluation validity agenda

Updated 2026-10-16 against `main` `1ece47014d05db898bf73afcd722a14524462e15`.
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

- **Status:** Open, unverified; no experiment or implementation is claimed.
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
- **Next test:** The Issue proposes a finite CPU-only synthetic T0 with
  wait-for-System-2, System-1-only, agreement-at-decision and
  agreement-conditioned bounded-continuation arms. Retain common-mode wrong
  agreement, stale/contradictory state, target change, authority loss,
  emergency preemption, expiry, release failure, irreversible action and
  unknown effect. An independent raw-only auditor must reconstruct task effect,
  decision gaps, lease revocation and every release obligation. The
  System-1-only arm is essential: if it performs equally, report
  `NO_INCREMENTAL_AGREEMENT_VALUE`. This is a proposed test, not a result or
  allocation; freeze exact source closure, output custody and mutation gates
  before any candidate run. No GUI, live input or model call is needed for T0.
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

## 10. Budgeted discovery of failures in shallow-zero task cells — #8914

- **Status:** Open and unverified; no PR, branch or result is recorded.
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
- **Next test:** Freeze the simulator, family split, features, attempt budget,
  reset contract, outcome oracle and independent audit before generating deep
  outcomes. Include null-signal, family-shift, leakage, repeat-dependence and
  reset-mismatch controls. No experiment is claimed.

## Priority and handoff

1. Continue #57's selected integrated path and resolve correctness/measurement
   blockers before spending remote-model budget on #6001 or #6035.
2. #8654's C07 audit is complete at method scope. Any follow-up must address
   C06's failed audit and make a distinct hypothesis decision; do not treat C07
   as evidence of agent adaptation or sampling benefit.
3. The lowest-cost untested discriminator in this family is #9004's finite
   common-mode-error comparison. It is independent of the consumed #6001
   allocations and does not need a GUI/model lane, but it still needs its own
   immutable freeze, candidate output and independent audit.
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
