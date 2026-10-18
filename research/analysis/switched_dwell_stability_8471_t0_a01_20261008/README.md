# Issue #8471 T0 A01 — finite switched-mode stability study

This additive package studies a finite exact-rational switched linear model. It does not modify the Agent Interface runtime and establishes no physical, product, actuator, GUI, or safety-authority claim. The issue explicitly excludes container setup; the experiment uses only the Python standard library on the host.

## H/T/D/C/U

- **H — hypothesis:** individually Schur-stable modes can produce unstable products and leave a declared finite envelope under unrestricted or hysteresis-only switching. An independently reconstructed multiple-Lyapunov prefix guard and minimum-dwell restriction should reject the exhibited unsafe cases while accepting a common-Lyapunov null control. Hysteresis alone need not constrain switching sufficiently. Dwell is a finite policy probe, not a general switched-system proof.
- **T — test:** enumerate all 2^12 binary mode words for the frozen pair A/B and x0=(1,1/2). Record exact-rational states, products, second-order Jury/Schur classification, every-prefix Lyapunov bound, and the strict infinity-envelope 4 result. Compare the hysteresis comparator (enter B at signal >=2/3, return A at <=1/3) and a 10-tick minimum-dwell controller. Also enumerate a common-Lyapunov pair, apply a fixed bounded additive disturbance to every word, exercise identity reset metadata, emergency-overrides-dwell metadata, and the strict equality boundary.
- **D — decision:** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all rows and counts, finds unstable/envelope-violating unrestricted words rejected by the strict Lyapunov guard, finds no certified unstable word, verifies every minimum-dwell schedule remains inside the finite declared envelope, accepts all common-Lyapunov rows, rejects all frozen mutations, and preserves strict equality as uncertified. Any false certificate or delayed abstract emergency override is `FAIL`; mismatched/missing data is `HOLD`.
- **C — controls:** fixed 12-step horizon and initial state; exact fractions; deterministic complete enumeration; independent `audit.py` (does not import candidate/protocol); exact Lyapunov identities and PSD comparison-factor checks; common-Lyapunov null; bounded-disturbance finite-response probe; reset and emergency control fixtures; equality boundary; seven mutation tests. Disturbance result does not establish ISS or robust stability.
- **U — limits:** two hand-authored modes, one initial state, one finite horizon, one envelope, and one switching policy do not establish general stability, a validated envelope for a physical system, safety requirements, sampled-data effects, continuous-time intersample behavior, implementation conformance, or runtime benefit. No GUI, hardware, actuator, model, or live setup is exercised. The primary theory context is average dwell-time stability, not an empirical result of this package: [Hespanha & Morse (1999)](https://web.ece.ucsb.edu/~hespanha/published/avedwell.pdf).

## Reproduction

From this directory, with CPython 3.11+ and no third-party packages:

```sh
python3 -m unittest -v test_construction.py  # construction iteration only; not the frozen run
python3 candidate.py                         # formal candidate: exactly once after freeze
python3 audit.py                             # independent formal audit: exactly once
```

The formal outputs, source hashes, environment, gate, and disposition are retained in `REPORT.md`, `FREEZE.json`, and the raw `candidate.json`. Construction tests are not formal candidate/auditor executions. Do not overwrite a formal output; a repaired protocol requires a new successor allocation.
