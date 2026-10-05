# Issue #7986 T0 A01 — formal method result

**Disposition: `PASS_METHOD_SCOPED`; frozen finite-model H is demonstrated.** The result is eight authored, integer-tick event rows only. It does not establish safety, harm reduction, a runtime policy, or live-interface behavior.

## Result

| Case | Observation age | Belief-error dwell | Unsafe-admissibility exposure | Realized unsafe effects | Result |
|---|---:|---:|---:|---:|---|
| Old observation, unchanged/correct belief | 10 | 0 | 0 | 0 | known |
| Stale belief after state transition | 10 | 6 | 6 | 0 | known |
| Fresh capture, wrong binding | 1 | 5 | 5 | 0 | known |
| No live authority | 8 | 0 | 0 | 0 | known |
| Revoked, no action opportunity | 8 | 0 | 0 | 0 | known |
| Forbidden action emitted | 10 | 8 | 8 | 1 (effect age 5) | known |
| Truth missing | 8 | unknown | unknown | unknown | `UNKNOWN` |
| Clock order ambiguous | unknown | unknown | unknown | unknown | `UNKNOWN` |

The candidate received no truth labels. Its raw file contains observation age and age-at-effect fields only. The separate auditor bound the full fixture to the frozen canonical digest, recomputed all age/effect fields, and adjudicated the truth-conditioned endpoints. It returned exit 0 with `passed=true`, eight cases, and zero errors. The old-but-correct case shows age alone is not exposure; the fresh/misbound case shows low age does not imply zero exposure. Potential unsafe exposure and realized unsafe effects remain distinct.

## Frozen allocation and execution

- Allocation: `7986-IBE-T0-A01-20261005-01`; base main `6a2826d391b77496b69752609a6f07b6971b4b6f`.
- Freeze UTC: `2026-10-05T04:48:40Z`; `FREEZE.json` SHA-256 `8a2dc7ce2fb30eeabedc1490e620b7106eb483d0a3f3005b4042334543dc419b`.
- Fixture canonical SHA-256: `1a9df8e83a7971cabf23fd240d01e2773b1202724c66c3ceae1191ff63a4407b`.
- Candidate command, exactly one formal invocation: `python -B research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/candidate.py research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/fixture.json research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/results/candidate.raw.json` (exit 0).
- Auditor command, exactly one formal invocation: `python -B research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/audit.py research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/fixture.json research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/results/candidate.raw.json research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/results/AUDIT.json research/analysis/incorrect_belief_exposure_7986_t0_a01_20261005/FREEZE.json` (exit 0; `{"passed": true, "errors": [], "case_count": 8}`). Retries: zero.
- Candidate raw SHA-256: `ec86e1c0f7029fa3f2e76eefba480a3055aeb1d278bcfc558e20aded5c07d26a`.
- Auditor output SHA-256: `3e4e79164b85577572b5cf468938636ae18ee9782d73f4036faa833f149c1094`.
- Construction tests were run before freeze, observed RED for the six missing behaviors, then GREEN 6/6. They include truth-sidecar hash mutation and candidate-raw mutation rejection.
- Host: macOS arm64, CPython 3.12.13. OrbStack was not retried: the same host's image-content store had already returned `operation not supported`. The frozen computation is standard-library-only; no container behavior is needed or claimed.

## Scope and limitations

The event fixture supplies one already-segmented maximal homogeneous interval per case. No interpolation, stochastic model, statistical estimate, independent human audit, GUI, model, external input, or runtime change was involved. The ground-truth sidecar is privileged and audit-only. T0 shows only that this finite metric implementation distinguishes its authored cases; it does not show the metric adds predictive or operational value beyond #5368/#6045/event-level signals. Truth quality, belief-set completeness, interval construction, clock domains, and action-class selection remain unvalidated.
