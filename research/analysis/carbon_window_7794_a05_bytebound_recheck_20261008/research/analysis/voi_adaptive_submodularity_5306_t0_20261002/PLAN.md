# T0 plan — conditional diminishing returns for VOI stopping

## H / T / D / C / U

**H.** Myopic one-check-at-a-time VOI stopping is not generally optimal when check outcomes are complementary: a test with zero immediate decision value can unlock positive value from a later test. Thus adaptive-submodular diminishing returns cannot be assumed for sequential verification without checking the actual evidence family. Safety, freshness, mandatory-check, and deadline gates must remain lexicographically prior to VOI.

**T.** A deterministic, exact-rational, no-model finite replay. In the primary binary diagnosis case, GOOD has prior 7/10 and BAD 3/10. Two conditionally independent tests A/B each return `-` with probabilities GOOD=2/5, BAD=2/3, and `+` otherwise. Each costs 1/100 decision-accuracy units; total budget is 1/50. Compare (i) myopic greedy net VOI, (ii) a fixed A-then-B checklist, and (iii) an independently enumerated exact Bellman policy. Measure conditional marginals for B before evidence and after A=`-`. A second case has a perfectly duplicated deterministic observation. Stale-generation and insufficient-deadline controls test that hard gates yield before optional checks.

The scoring objective is expected exact binary classification accuracy minus declared check cost. This is a deliberately finite method fixture; it is not a model of calibrated interface-risk probabilities. An independent auditor recomputes the predictive distribution, all reachable conditional marginals, policy value, and hard-gate outcomes from `model.json` and candidate output without importing candidate code.

**D.** `COUNTEREXAMPLE_GREEDY_VOI_SCOPED` only if exact enumeration establishes (a) a conditional marginal increase for B after A=`-` versus before evidence, (b) the myopic policy stops at the root, (c) an exact feasible policy has strictly higher expected net value than STOP, (d) the duplicate negative control has non-increasing marginal value, (e) stale/deadline controls return YIELD with zero optional calls, and (f) independent audit and mutation tests pass. If any identity, probability, or policy calculation is ambiguous, HOLD. No broad claim that all VOI or all greedy policies fail.

**C.** Fixed mandatory verification or a more expressive multi-step VOI policy may be preferable; real checks may lack known likelihoods or be correlated/nonstationary. This fixture does not compare live verifier implementations.

**U.** No real adapter, verifier, model, GUI, user data, network, task effect, latency, calibration, or safety outcome is measured. The posterior probabilities and test costs are constructed. The result only falsifies a universal diminishing-return assumption for this declared finite decision model.

## Frozen interfaces and execution

- Candidate-visible input: `model.json` (priors, conditional outcome likelihoods, declared costs/budgets, and gate-control metadata).
- Candidate: `candidate.py`; it cannot import or read `audit.py`.
- Independent raw-only scorer: `audit.py`; exact arithmetic uses Python `Fraction` and does not import candidate functions.
- Contract/mutation suite: `test_contract.py`.
- Formal commands after freeze: `python candidate.py`, `python audit.py`, `python -B -m unittest -v test_contract.py`. Candidate and auditor each one invocation; retries 0.
- Construction checks are logged separately. Host-only execution is permitted because the arithmetic fixture needs no external service, while the shared Docker/OrbStack lane is recorded occupied and the local Docker Desktop service is not startable by this user process. No container will be touched.

