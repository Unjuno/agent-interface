# A02 construction result

Disposition: `PASS_CONSTRUCTION_SCOPED`; no formal allocation was run.

- Frozen construction fixture: 32 cohorts × 40 rows = 1,280 assignments; seed 7993002.
- Candidate and oracle fixtures are distinct objects/files at the protocol boundary; candidate input has only X, propensity, follow-up, and observed label (null when unresolved). Oracle digest is checked by the auditor.
- Candidate returns `ASSUMPTION_CONDITIONAL` for eligible support and `UNKNOWN` for missing assumptions, positivity failure, invalid/hidden labels, or empty observed cohort.
- Auditor independently reconstructs every cohort's complete-case and HT value; it detects missing rows, changed hidden truth under oracle SHA, propensity mismatch, and candidate-output mutation.
- Ordinary construction tests: 11/11 PASS. Optimized (`python3 -O`) construction tests: 11/11 PASS.
- Fixture execution: candidate `ASSUMPTION_CONDITIONAL`; auditor `ok=true`, `errors=[]`, 1,280 assigned, 32 cohorts reconstructed.
- Environment: host macOS Python 3.14.5, standard library. No container ran; no pinned-image pull or OrbStack repair attempted. No separate CPU/container allocation was identified.

Limit: source-level construction validation is not the independent review of a formal frozen 20,000-cohort execution. This result makes no claim about real verifier-risk calibration, censoring-model validity, finite-sample guarantees, production behavior, safety, or authority. Preserve the earlier A01 and PR #8034 history unchanged.
