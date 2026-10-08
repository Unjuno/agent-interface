# Issue #8630 — reserve-binding diagnostic after T0 A01

**Disposition: `PASS_DIAGNOSTIC` for the authored construction only.** This is a new exact-arithmetic diagnostic, not a formal allocation or a correction of A01. A01 remains `FAIL_METHOD` as recorded in its original report and draft PR #8744.

## Finding

A01's weak-signal arm did not contain the intended opportunity competition. Under its four-opportunity horizon, skipping observation used one action, mandatory verification and one recovery attempt, leaving one opportunity idle. The recorded scores were 0.755 for observe+recover and 0.750 for skip+recover, so observation correctly won that fixture.

This diagnostic keeps A01's prior, action-success matrices, one-opportunity observation/action/verification costs, horizon, perfect type observation, and 0.5 recovery success probability. It changes one explicitly declared factor: when observation is skipped, the freed opportunity can fund a second independent recovery attempt. At least one recovery attempt and the mandatory verification remain feasible under both strategies.

| Regime | No-observation action success | Observed action success | Joint choice | Joint score | Always observe | Never observe |
|---|---:|---:|---|---:|---:|---:|
| Informative | 0.55 | 0.90 | Observe + one recovery | 0.95 (19/20) | 0.95 | 0.8875 (71/80) |
| Weak signal | 0.50 | 0.51 | Skip + two recoveries | 0.875 (7/8) | 0.755 (151/200) | 0.875 |

With observation success `q1`, no-observation success `q0`, and recovery success `r`, observing is better here exactly when `q1 > q0 + (1-q0)r`. The threshold is 0.775 for the informative case and 0.75 for the weak case. Thus this declared model produces the intended switch while retaining one recovery opportunity and mandatory readback in every policy.

The closed-form calculator and a separate path enumerator agree on all 8 feasible policies in each regime. Both fixed schedules lose strictly in at least one regime; the joint optimum ties the better fixed schedule in each respective regime. Normal and optimized construction tests pass 4/4.

## Interpretation and limits

This diagnoses why A01's frozen weak-signal gate failed and demonstrates a small mathematical condition under which information can be worth a recovery opportunity. The result depends on perfect observation, authored action probabilities, independent repeated recoveries, unit opportunity costs and a binary verified-success objective. Equal weighting or calibration of the two regimes is not asserted. The result does not validate the general #8630 hypothesis, a real GUI hazard model, safety, latency, model behavior, token savings, or product benefit. No private live lane or formal allocation was used; no A01 candidate/auditor was rerun.

The first shell redirection attempt could not open `run-01/candidate.json` because the output directory did not yet exist; the calculator process did not start. After creating the dedicated directory, the calculator and independent enumerator each ran once, with outputs retained below `run-01/`.

Reproduce the construction checks and diagnostic from this directory:

```text
python3 -B -m unittest discover -s . -p 'test_*.py' -v
python3 -B -O -m unittest discover -s . -p 'test_*.py' -v
python3 -B diagnostic.py > run-01/candidate.json
python3 -B enumerate_oracle.py < run-01/candidate.json > run-01/oracle.json
```

See [MODEL.json](MODEL.json), [run record](RUN_RECORD.md), raw rows and oracle summary in `run-01/`, and [SHA256SUMS.txt](SHA256SUMS.txt).
