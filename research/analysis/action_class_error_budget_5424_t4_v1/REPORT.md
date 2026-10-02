# Issue #5424 T4 — ranking inversion with a hard-catastrophe control

**Disposition: `PASS_METHOD_SCOPED`.** A frozen deterministic host-CPU candidate generated 80 historical rows and 128 held-out outcome rows. An independently implemented raw-only auditor reconstructed every row and summary, with no mismatches, and rejected all 5 preregistered corruptions. This validates only the finite method and fixture contract; it does not establish a production error budget, calibrated severity weights, or net safety benefit.

## Hypothesis and result

With equal 40-offer histories, the unweighted threshold freezes route A after 8 recoverable failures but leaves route B active after one catastrophic plus one recoverable failure. The ordinal score and separate hard-catastrophe gate freeze B. In the 8-offer continuation, both B gates prevented the two scripted catastrophic primary effects; count-only allowed both. This is the predicted severity-ranking inversion on this hand-authored trace.

| Policy | Route A history (count/points) | Route B history (count/points) | B frozen at boundary? | B primary catastrophes executed (independent-safe / incident-correlated) |
|---|---:|---:|---:|---:|
| Unweighted count | 8 / 8 | 2 / 11 | no | 2 / 2 |
| Ordinal severity | 8 / 8 | 2 / 11 | yes | 0 / 0 |
| Hard catastrophic event | 8 / 8 | 2 / 11 | yes | 0 / 0 |

The current-generation two-probe quorum resumes frozen routes at step 6. All 16 held-out offers per scenario remain represented. Under incident-correlated fallback, hard-freezing B reduces primary catastrophes from 2 to 0 but raises severe fallback events from 2 to 3 and lowers completed offers from 6 to 5. The control therefore exposes a concrete primary-versus-fallback tradeoff and does not make fallback safe; the two fallback regimes and primary outcomes are reported separately in raw data. `NO_FREEZE` is an exposure control, not a deployable recommendation.

## Audit and reproducibility

- Frozen main: `43f7cd88d91af05036fae2100ec4e155c59e105c`; allocation: `ACTION-ERROR-BUDGET-5424-T4-RANKING-INVERSION-HOSTCPU-20261003-01`.
- Candidate: one invocation, exit 0; 80 history rows, 128 continuation rows. Candidate raw SHA-256: `45a05a6a1c024790c6016329a05b1d9349dc47749159a66f70400bc17ddd0ce8`.
- Independent auditor: one invocation, exit 0, `PASS_METHOD_SCOPED`; 80/80 history and 128/128 outcome rows independently reconstructed, 0 mismatches, 5/5 corruption controls rejected.
- Candidate catastrophic-primary count for route B: hard gate 0; unweighted count 2.
- Freeze and full invocation receipts are in [`FREEZE.json`](FREEZE.json) and [`RUN_RECORD.json`](RUN_RECORD.json); full rows and auditor receipt are in [`raw/formal_01/`](raw/formal_01/).

## H / T / D / C / U and limits

The tested claim is exactly the finite inversion and exposure contrast above. Weights (`ok=0`, `recoverable=1`, `severe=4`, `catastrophic=10`), thresholds, histories, continuation outcomes, and fallback dependence are authored fixture values, not empirically estimated. Counterfactual primary values while frozen are oracle-only and censored from policy input. No natural event frequencies, stationarity, route attribution, user outcomes, safe fallback availability, SLO, production benefit, or safety certification is inferred. The count threshold is deliberately shown as a control; no scalar score replaces the non-compensable hard-catastrophe gate.

No model, GPU/CUDA, GUI, Docker/WSL, network, or repository runtime was used. T4 is additive: earlier T2/T3 reports and allocations are unchanged.
