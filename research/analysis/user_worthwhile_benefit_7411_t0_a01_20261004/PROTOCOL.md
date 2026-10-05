# Issue #7411 T0 preregistration — A01

## Question and boundary

Can a simple monotone preference estimator recover known heterogeneous minimum worthwhile savings from synthetic paired-choice records, report `UNKNOWN` when the dose support never crosses the decision point, and keep user preference from overriding a hard correctness regression? This is a method test only. Synthetic records do not establish human preferences, route effects, or product value.

## H / T / D / C / U

**H.** On a finite synthetic dataset with a known heterogeneous threshold distribution, the frozen estimator will recover the median minimum worthwhile time saving separately for planner-boundary waits and local processing within 2 seconds, retain ties and missing answers without treating either as a positive choice, and abstain when the observed dose support does not identify a 50% choice crossing. A seeded correctness regression must keep the route ineligible regardless of preference.

**T.** Generate 160 paired synthetic respondents, each crossed over two timing locations (planner-boundary and local-processing), at 13 savings doses from 0 to 24 seconds in 2-second steps. The same respondent threshold is used for both locations; local-processing thresholds are exactly 4 seconds higher. Individual planner-boundary thresholds are deterministic, balanced values from 6 to 14 seconds, so the population medians are 10 and 14 seconds. Generate choices with frozen logistic response noise (scale 1.5 seconds), 4% lapse probability, 8% ties, and 2% missing responses using seed 7411001. Keep objective savings and task facts paired across timing-location rows. Add a low-support control whose observations stop at 6 seconds and whose choices stay below 50%, plus a route-preference/correctness control in which high preference cannot authorize an objectively incorrect route.

**D.** `PASS_METHOD_SCOPED` only if the candidate estimates both supported median thresholds within 2 seconds of their frozen truths; returns `UNKNOWN` for the low-support control; preserves exact cross-location dose parity; never counts tie/missing as a positive preference; and marks the correctness-regression control ineligible. The independent auditor must reconstruct every raw record, reproduce the threshold estimates and gates, and reject all four frozen mutations (changed dose, timing-location relabel, response changed to a fabricated positive, and correctness gate flipped). Any failure is retained without retry. No synthetic pass supports a human or route-benefit claim.

**C.** A simple aggregate response curve can hide subgroup variation; lapse/noise or sparse support can make a single threshold unstable. Equal savings may be valued differently depending on where the wait occurs, but this fixture cannot establish why.

**U.** Threshold values and responses are simulated. No participant, real application, model, GUI, user-valued threshold, adoption decision, task effect, or safety property is measured. The test does not validate an estimator for real HCI data.

## Frozen execution

- One candidate invocation and one independently implemented audit invocation; no retries.
- Standard-library Python, host-only, no external data/network/application access.
- Candidate writes `formal_01/raw.json` and `formal_01/candidate.json`; auditor writes `formal_01/audit.json`.
- Exact invocations, from the repository root: `python3 -B research/analysis/user_worthwhile_benefit_7411_t0_a01_20261004/candidate.py` then `python3 -B research/analysis/user_worthwhile_benefit_7411_t0_a01_20261004/audit.py`.
- Required fields and exact commands are encoded in the frozen scripts. Inputs and scripts are hashed in `FREEZE.json` before formal execution.
- OrbStack was read-only inspected before freeze. `docker info` returned Engine 29.4.0 linux/aarch64, but inspecting the cached `python:3.12-slim` image failed on a missing content blob with `operation not supported`. No image pull/build/container action was attempted. The frozen test is a deterministic standard-library method test; its execution will be explicitly classified host-only and provides no container-isolation evidence.
