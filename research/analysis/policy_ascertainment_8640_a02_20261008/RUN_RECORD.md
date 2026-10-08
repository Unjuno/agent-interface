# A02 run record — Issue #8640

Allocation: issue-8640-method-a02
Branch: research/8640-ascertainment-a02-20261008
Main source base: 99f2521811df790db3c96cdfa9313a6296f247f7
Execution: candidate source fetched from this branch and evaluated once in an isolated JavaScript V8 compute call; independent auditor source fetched and run once in a separate V8 call. No filesystem or external service was used for the calculation. This is the exact finite, no-runtime T0 in the freeze, not an OS/container experiment.
Candidate source Git blob SHA: d58507dd3bd1759c009be13a464de11c19d6343d
Independent auditor source Git blob SHA: 5f704517c0eb5e659ccad99f49e69925821bc375
Freeze commit: 66518eb3c76765ef0e1a81c5bd889780996bc69f
Candidate commit: 49f9c3311605ebdbcce96deff0f739088be58898
Auditor commit: 176d3c6bc964577c1fc547a39a09c0c283803146

## Result

PASS_METHOD_SCOPED. The raw ledger contains 20,480 worlds (4,096 per scenario), enumerating all 16 blocked assignments × 256 observation masks in each of five scenarios. Independent raw-only audit reconstructed every world; probability mass was 1 within floating-point roundoff for each scenario; finite-population bounds covered truth in all worlds; five frozen corruptions were rejected.

- Complete, invariant ascertainment: true A/B means 0.75/0.25; resolved-only means 0.75/0.25; reversal probability 0; logged IPW expectation 0.75/0.25.
- Logged, route-dependent ascertainment: resolved-only conditional means 0.07253125/0.25 and rank reversal probability 0.857375. With the correctly logged positive probabilities, expected IPW was 0.7500000000000003/0.25000000000000033 (roundoff from the exact finite sums).
- Fixed-horizon censoring: resolved-only means 0/1, reversal probability 1. Because inclusion probability is zero for some route-units, IPW is undefined for both routes; do not infer a point estimate.
- Zero-probability stratum: true means 0.25/0.5, resolved-only means 1/0.5, but route A IPW is undefined; bounds cover truth.
- Hidden/misspecified selection probability: logged-IPW expected estimate for A is 0.15 against truth 0.75 (bias -0.60); B is 0.25 against 0.25. Positive logged values alone do not repair misspecification.

All estimates are synthetic finite-population arithmetic. No historical repository result, live interface route, safety, causal effect, human benefit, or production estimator is validated.

## Integrity and limits

Raw ledger: candidate_raw.json (Git blob SHA: 18be4fe82a61a231617ae6e10dfda7c89b3fdfc3).
Audit: audit.json (Git blob SHA: 35b5da9832af5cc1769f2cb4643c485ae4c9cd17).
Original A01 infrastructure STOP remains unchanged in Issue #8640; it is not included in A02's scientific sample and was not retried.
