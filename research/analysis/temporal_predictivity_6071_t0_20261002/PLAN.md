# Issue #6071 T0 — temporal-predictivity schedule integrity

## H / T / D / C / U

- **H:** A finite three-arm schedule can isolate response-delay predictivity from marginal delay distribution, response-type counts, vignette content, and machine-effect truth; a constant-delay arm provides only a variance benchmark.
- **T:** Sixteen paired synthetic vignettes, eight `READY_TO_REVIEW` and eight `NEEDS_HUMAN_DECISION`; A constant 5-second delay; B and C share eight 2-second and eight 8-second delays; B balances short/long within each response type, C deterministically associates each type with one delay. Verify type entropy, mutual information, assignment/task/content/effect invariance, arm-order counterbalance, and forward/reverse task-order type balance. Independent auditor reconstructs each condition from the raw frozen table.
- **D:** `METHOD_PASS_SCOPED` only if A/B/C have identical task/content/effect truth and type counts; B/C have exactly the same delay multiset and mean; B has zero empirical timing/type mutual information; C has 1 bit; A has zero variance; counterbalance schedules are balanced; and corruption controls flag changed effect/content, timing leakage in B, altered delay mass, deadline or authority differences.
- **C:** An explicit truthful status cue may outperform timing predictivity; only a human study can establish behavior. A/C differ in variance as well as predictivity, so only B–C isolates predictivity.
- **U:** This no-participant T0 tests schedule construction only. It cannot show that timing is perceived, useful, ethical, accessible, or causally changes human action. No intentional delay policy is proposed.

## Prior-art boundary

Weber, Haering & Thomaschke (2013) manipulated response-time length/variability in simulated sequential office tasks. Thomaschke & Haering (2014; N=122) reported faster choice responses under deterministic delay predictivity than constant, nonpredictive, or probabilistically predictive conditions, with matched total delays across variable groups. Those studies motivate the contrast but do not establish an AI-agent or GUI takeover benefit; this T0 recruits no people. Primary links: [Human Factors DOI](https://doi.org/10.1177/0018720813475812); [IJHCS DOI](https://doi.org/10.1016/j.ijhcs.2013.12.004).

## Execution boundary

Source base `abd0ce6425e24934731b763ece83421d309535b5`; additive research path. Run construction mutation controls first, then freeze and invoke candidate/auditor once each. Host CPython, no Docker isolation claim (Docker Engine unavailable), no model/provider, GUI, network experiment, participant, user data, or consequential action. Never encode correctness, authority, emergency status, or release in delay.
