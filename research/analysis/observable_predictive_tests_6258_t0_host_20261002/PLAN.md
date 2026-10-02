# Issue #6258 — observable predictive-test state T0 (host fallback)

## Question and scope

For a bounded finite interface family, can vectors of predictions over permitted observable tests preserve action-relevant history distinctions while safely merging a null pair, without confusing test-prediction equality with external-effect identifiability, route conformance, or unbounded behavioral equivalence?

This is a finite synthetic method experiment. It does not probe a real GUI or user application. The candidate receives only observable test predictions and claim/test-vocabulary metadata; an independently authored auditor carries the hidden transition/effect and safe-action oracle. No oracle-only hidden-state label is available to the candidate.

## H / T / D / C / U

**H.** Screenshot and last-one-observation history can alias two histories with different safe-action sets. A bounded observable-test representation must keep that seeded pair separate or HOLD when no permitted independent fresh effect receipt exists; use a fresh independent receipt to separate the effect-complete arm; safely merge a null pair with identical safe-action sets; and limit a delayed discriminator to the stated horizon. Forbidden probes, stale/source-correlated receipts, external generation changes, and cross-route hard-label mismatches must never become merge or authority evidence. A correctly specified finite latent-state baseline may retain hidden distinctions, while full-history equivalence conservatively keeps distinct histories separate.

**T.** Allocation `OBSERVABLE-PREDICTIVE-TESTS-6258-T0-HOST-20261002-01`, base `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`, additive branch `research/6258-predictive-tests-t0-host-20261002`, path `research/analysis/observable_predictive_tests_6258_t0_host_20261002/`. Enumerate every permitted action-test word of lengths 1 and 2 for the silent-effect alias, fresh-receipt positive arm, and null arm (six words per arm), plus both prefixes for the delayed arm. The separate auditor reconstructs each output from its own finite transition table and independently checks the safe-action sets. Additional fixed controls cover forbidden-only discrimination, stale and source-correlated receipts, external mutation/generation invalidation, and route hard-label mismatch. Compare screenshot, last-one history, oracle-informed finite latent belief, full history, and predictive-test grouping without treating them as interchangeable notions.

Docker/OrbStack was not used: the current Docker endpoint timed out, Docker service is stopped per the latest owner snapshot, and #5085 has no exclusive allocation for this task; existing shared container inventory is UNKNOWN. No service, image, container, GPU, WSL distro, or other owner allocation was started, stopped, or changed. This host fallback changes only the reproducibility scope. No network, GUI, application, model, physical input, user data, or effectful action is involved.

**D.** `PASS_METHOD_SCOPED` only if the independent raw-only auditor enumerates/replays the complete frozen test-word sets; detects the silent-effect safe-action mismatch and the candidate refuses merge; recognizes the fresh independent receipt as a separating observation; confirms the null pair has equal oracle safe-action sets and is merged; confirms the horizon-2 delayed pair is not claimed equivalent beyond step 2; and all negative controls remain fail-closed. Missing rows, altered predictions, unsafe merge, invalid receipt acceptance, forbidden probe, stale-generation reuse, or route-equivalence overclaim is `FAIL_AUDIT`/`FAIL_UNSAFE_ALIAS`. Runtime/freeze/output integrity problems are `STOP`. One formal candidate CLI invocation and one audit invocation only; retries 0.

**C.** Deterministic, authored finite fixture and Python standard library only. Candidate forecasts are supplied fixture observations, not learned probabilities. Candidate and auditor code use different representations; the auditor does not import candidate code. Host scheduling is not an outcome variable.

**U.** Does not establish learnability/calibration from sparse traces, PSR theory beyond the fixture, completeness of any real test vocabulary, long-horizon behavior, dynamic or nonstationary GUI state, real external-effect receipt quality, action authority, route equivalence/conformance, production safety, or live utility. The latent-state baseline is an oracle-informed comparator, not an implementable candidate.

## Freeze and commands

- Environment: Windows 11 x64, CPython 3.12.10, stdlib only.
- Construction command: `python -B -m unittest discover -s research/analysis/observable_predictive_tests_6258_t0_host_20261002 -p 'test_*.py' -v` — observed 16/16 PASS before freeze.
- Syntax check: `python -B -m py_compile research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.py research/analysis/observable_predictive_tests_6258_t0_host_20261002/audit.py`.
- Candidate (one formal invocation): `python -B research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.py --output research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.raw.json`.
- Auditor (one formal invocation, only after candidate exit 0): `python -B research/analysis/observable_predictive_tests_6258_t0_host_20261002/audit.py research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.raw.json --output research/analysis/observable_predictive_tests_6258_t0_host_20261002/audit.raw.json`.
- Candidate/auditor raw formal output paths must be absent before launch. No retry or source modification after preregistration; preserve any failure as-is.
- Exact candidate, auditor, test and plan hashes, formal invocation counts and retry budget are in `FREEZE.json`.
