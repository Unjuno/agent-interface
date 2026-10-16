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
5. Return each result to its source Issue and this family map. Preserve all
   earlier STOP, FAIL, HOLD and PASS records; do not close an idea because its
   summary has been written here.
