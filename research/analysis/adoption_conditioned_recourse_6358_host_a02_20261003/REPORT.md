# Issue #6358 — local T0 A02 result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen deterministic cohort fixture produced the preregistered high-adoption shared-capacity contrast, and a separate raw-only auditor reconstructed all 56 case/policy ledgers with zero errors. This is a synthetic method result only.

## Question and frozen method

Issue #6358 asks whether advice that is feasible for each offered stop can become collectively infeasible when recipients adopt it against finite shared recovery capacity, and whether adoption-conditioned advice can preserve resolved outcomes without suppressing work or relaxing safety. This allocation compared seven advisory/control policies over eight fixed cases (four offered stops per case; 56 ledgers total). It used no model, GUI, human participant, network, GPU, container, production service, or actual retry/actuation.

Allocation: `ADOPTION-CONDITIONED-RECOURSE-6358-T0-MAC-HOST-20261003-02`
Main frozen before execution: `fc1c09294458d3b2744fa05432d4cf8a19583f18`
Runtime: macOS 26.6.2 arm64, CPython 3.14.5, standard library only.
Candidate exit: 0, one invocation. Auditor exit: 0, one invocation after candidate exit 0. Retries: 0.

The candidate raw records are immutable at `results/formal-02/candidate.raw.json`; the independent result is `results/formal-02/audit.raw.json`. The audit reports `PASS_METHOD_SCOPED`, 8 cases, 56 policies, `errors=[]`. Raw SHA-256 values are in `SHA256SUMS`.

## Results

Resolved offers by policy in the primary shared/high-adoption case (denominator is four offered stops in every arm):

| Policy | Independently verified resolved | Other relevant outcome |
|---|---:|---|
| Generic retry | 2/4 | 2 explicit `NO_FEASIBLE_RECOURSE` |
| Individual witness only | 2/4 | 2 explicit `NO_FEASIBLE_RECOURSE` |
| Public warning + bounded stagger | 2/4 | 2 explicit `NO_FEASIBLE_RECOURSE` |
| Wording-only placebo | 2/4 | Routes and outcomes identical to generic retry |
| Recipient-specific authorized routing | 4/4 | Flexible class 2/2; shared-only class 2/2 |
| No-advice typed stop | 0/4 | Four conservative stops; no work attempted |
| Abandon-eligible control | 2/4 | Two eligible offers explicitly retained as suppressed/unresolved |

The policy discriminator appears only when capacity is shared and adoption is high. Recipient-specific routing resolves 2/4 in the low-adoption case and 4/4 in the disjoint-resource null; the disjoint null does not show an advantage over other active advice arms. In the no-feasible case it resolves 1/4 and reports three no-route outcomes. In the forbidden-alternative case it resolves 3/4 while unsafe/forbidden executions remain zero. In the slow-alternative case it resolves 2/4 and rejects deadline-infeasible routing. Expired advice remains `STALE_ADVICE` with no attempts; uncertain delivery remains `UNKNOWN_NO_RETRY` with no attempts.

The auditor verifies all offered IDs and denominators, the per-offer advice budget, authority/idempotency/receipt sequence, capacity, deadlines, class-stratified outcomes, placebo invariance, route authorization, and the frozen primary and control counts. The 16-test candidate/auditor construction suite passed before the run and was rerun after it; corruption controls reject dropped/censored offers, forbidden routes, over-capacity overlaps, expired work, uncertain-effect retries, changed fixture identity, and placebo outcome changes.

## Provenance and limits

The frozen source and case hashes are in `FREEZE.json`. Candidate raw SHA-256 is `78cbeb299018b9e0d711ecf41eead90a1568df1de51ea9dd4a01758df59fea38`; independent audit SHA-256 is `0c9dc102ef1387f899e616b694043c4a029b1d67fb66fc45fbc959dce3837628`. Candidate and auditor stdout/stderr and exact argv are retained under `results/formal-02/`.

This is one authored finite synthetic fixture, not a randomized or repeated cohort study. It does not demonstrate real advice adoption, general human/agent behavior, causal prevalence, real queue dynamics, production capacity, or end-to-end task benefit. The external recourse/congestion analogies remain bounded inspiration, not transferred theorems.

Predecessor allocation-01 `STOP_RUNNER_REDIRECTION_DIRECTORY_MISSING` and local A01 `STOP_RUNNER_OUTPUT_PARENT_MISSING` remain unchanged in their respective records. Neither started a candidate process; neither has been relabeled or retried. Their failures are runner/setup evidence, not negative scientific findings.
