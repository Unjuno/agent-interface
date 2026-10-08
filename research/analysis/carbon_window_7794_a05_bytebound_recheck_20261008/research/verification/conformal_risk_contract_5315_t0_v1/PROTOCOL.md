# Issue #5315 — conformal risk contract boundary T0

Status before execution: frozen design; one bounded deterministic host-only
experiment. This is not a Docker allocation, runtime change, or live-task test.

## H / T / D / C / U

**H — hypothesis.** A conformal risk certificate is safe to expose only for
the exact risk functional and assumptions its method supports. In particular,
ordinary CRC's bounded monotone-loss guarantee for marginal expected risk must
not be interpreted as conditional risk among emitted singleton claims. A
checker that binds population, calibration digest, version, freshness, and
assumption status will reject a conditional-selective CRC claim and any
declared mismatch; rejected claims yield UNCERTAIN/set-valued output and never
grant authority.

**T — test.** Exact finite fixture with 1,000 evaluation rows in five declared
arms (IID reference, temporal, UI/layout, task-family, adaptive-query). In the
IID reference, 40 high-score rows are all wrong singleton claims, so their
population loss is 0.04 while their conditional selective risk is 1.00. The
calibration record contains 8 errors in 199 examples, target alpha 0.05, and
bounded loss B=1; compute the classic CRC finite-sample upper expression
`n/(n+1)*Rhat + B/(n+1)` exactly. Compare raw-score, deterministic-checklist,
CRC-marginal, fail-closed calibrated singleton, and set-valued outputs. Apply
five corruption controls to the certificate checker. The shifted/adaptive
arms are explicit counterexamples to applicability, not samples from a
claimed natural distribution.

**D — decision gates.** PASS this scoped T0 only if (1) the marginal arithmetic
matches an independently coded raw-only oracle; (2) the IID witness has
marginal risk <= alpha and conditional selected risk > alpha; (3) the checker
permits only the supported marginal CRC scope and rejects conditional scope,
each shifted arm, and every corruption control; (4) no result can grant effect
or action authority. Any mismatch is FAIL; missing/stale inputs are HOLD.
PASS does not mean calibrated singleton selective risk is solved.

**C — cost/risk.** Deterministic standard-library calculation over 5,000 rows;
no model, GUI, external effect, network, GPU, or package installation. Main
risks are confusing the classic CRC marginal guarantee with selective risk,
and overreading a hand-constructed finite fixture as population evidence.

**U — unknowns.** SCRC's exact transductive/symmetric-selection algorithm and
conditional-exchangeability gates are not implemented here; no calibration
corpus is representative; shift detection is supplied as a declared fixture
fact, not learned; no confidence interval for real workloads, task correctness,
runtime integration, or causal/effect authority is established.

## Frozen assumptions and execution

- Frozen main: `70b69b47845b35afde59c2a5f0b56c6f906c6904`.
- Issue: https://github.com/Unjuno/agent-interface/issues/5315.
- Primary method sources: CRC, https://arxiv.org/abs/2208.02814; SCRC,
  https://arxiv.org/abs/2512.12844.
- Classic CRC scope used here: exchangeable observations, bounded loss, and
  the method's monotonicity conditions; its expectation is not conditional
  selective risk. SCRC's selective result relies on symmetric selection and
  conditional exchangeability of the selected calibration/test subset.
- Fixture is fixed in `scenarios.json`; no seed, tuning, retries, or excluded
  rows. The experiment runs once after source commit. Independent audit reads
  only raw JSON and re-derives counts/formula without importing candidate code.
- Container execution is not authorized by the current shared Docker/CPU
  coordination record (#5085); therefore this is explicitly host-only. No
  container was launched and no shared resources were inspected or modified.

## Non-authority boundary

Certificates only shape claims. They do not establish a real task result,
external effect, freshness, release, lineage, or permission to act. The
set-valued fallback is descriptive and not an admission token.
