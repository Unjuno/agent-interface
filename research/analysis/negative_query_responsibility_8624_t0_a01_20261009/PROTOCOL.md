# Issue #8624 T0 A01 protocol

## H / T / D / C / U

**H —** For each frozen finite stratified Boolean rule system, the compatible prime-implicant pair construction recovers the same actual causes, minimum contingency sizes, responsibilities, and robustness radius as direct exhaustive intervention enumeration. It represents currently absent facts with explicit negative literals, agrees with a positive-support control on the monotone case, distinguishes two negative-query models with identical minimal positive supports and inclusion-minimal answer-flip sets, and returns UNKNOWN_TOO_LARGE rather than an incomplete prime explanation when the full cube scan exceeds the fixed budget.

**T —** Evaluate seven authored rule systems over their complete finite mutable universes. The candidate enumerates every state, computes minimal positive supports and inclusion-minimal outcome-changing interventions, enumerates prime implicants only when 3^|U| <= 100000, and applies the compatible-prime-pair characterization. A separately implemented auditor reconstructs every state from the stratified rules, enumerates every candidate-specific contingency directly, computes supports/flips independently, and derives prime implicants using iterative Quine–McCluskey combination. It compares every cause, minimum contingency witness, responsibility, and radius. The frozen input contains a monotone positive control, the negative-result example with an absent prerequisite, a direct present-exception case, a pair with equal support/flip summaries but different causes, the radius-one/contingency-three case, and an eleven-fact parity complexity control.

Formal order is exactly one candidate invocation followed by exactly one raw-only auditor invocation, and only if the candidate exits zero and leaves nonempty raw output. There are no retries. The formal command uses the host's standard-library Python because this protocol requires no Engine API, GUI, model, external data, or container isolation. An optional pre-freeze Docker availability probe is recorded separately and is not an experiment result or an eligibility gate.

**D —** PASS_METHOD_SCOPED requires exact candidate/auditor agreement on every enumerated row and cause quantity; explicit negative literals; matching positive-control and paired-summary behavior; rejection of all frozen corruptions; and an explicit, complete UNKNOWN_TOO_LARGE response for the dense prime analysis. Any discrepancy is FAIL_METHOD. An invalid stratum/domain or source-identity mismatch is STOP. The dense candidate's refusal is not counted as a completed responsibility result.

**C —** Per-fact positive supports, nearest flips, and typed query completeness may already be sufficient for every decision that matters; a causal diagnostic could add complexity without changing a safe choice. An apparently pivotal fact can also be an artifact of an arbitrary mutable-fact universe.

**U —** The fixture is hand-authored and deterministic. It does not establish that a screenshot candidate universe is complete, that a missing visual object is an observed absent fact, that any UI query was valid or fresh, or that a synthetic toggle is an authorized real action. No probability, production frequency, GUI behavior, runtime safety, or user benefit is inferred.

## Frozen semantics

Each case defines a finite set U of mutable Boolean extensional facts, an observed state E subset-of U, safe ground nullary rules with explicit strata, and the Boolean endpoint Goal. An intervention toggles membership of selected facts in E. For observed result b, fact tau is a cause when some Gamma subset-of U excluding tau preserves b and toggling tau afterward changes the result to 1-b; kappa_E(tau) is the minimum size of such a contingency and responsibility is 1/(kappa+1), or zero when no contingency exists. Robustness is the minimum number of toggles that reverse the observed answer.

The candidate enumerates all ternary cubes over the finite universe for prime implicants, with an explicit full-scan bound. The independent auditor uses a different implicant construction and a direct intervention oracle. This is a bounded implementation check of the transfer claim, not an independent validation of the source paper.

## Method references

- Thapa & Staab, [Causal Explanations for Stratified Datalog](https://arxiv.org/abs/2608.21141), especially the finite intervention semantics and compatible-prime-pair characterization of minimum contingencies.
- Bienvenu, Figueira & Lafourcade, [Responsibility Measures for Conjunctive Queries with Negation](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICDT.2026.20), cited in Issue #8624 for the separate signed-fact explanation choice. This experiment does not implement or claim equivalence with their responsibility measures.
