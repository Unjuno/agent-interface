# Issue #6258 T0 result — host-only, method-scoped

## Disposition

`PASS_METHOD_SCOPED`. Candidate and independent auditor each ran once after the preregistration comment; retries 0. The candidate had no access to hidden-state/effect-oracle labels. The separate auditor replayed the bounded transition deck and checked the independent safe-action oracle with zero mismatches.

## Executed experiment

- Allocation: `OBSERVABLE-PREDICTIVE-TESTS-6258-T0-HOST-20261002-01`.
- Frozen base: `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`; freeze commit: `99dc7131a589c3ca8427ed49a261eff9045bd5f1`.
- Construction: `python -B -m unittest discover -s research/analysis/observable_predictive_tests_6258_t0_host_20261002 -p 'test_*.py' -v` — PASS, 16/16.
- Candidate: `python -B research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.py --output research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.raw.json` — exit 0, one invocation.
- Auditor: `python -B research/analysis/observable_predictive_tests_6258_t0_host_20261002/audit.py research/analysis/observable_predictive_tests_6258_t0_host_20261002/candidate.raw.json --output research/analysis/observable_predictive_tests_6258_t0_host_20261002/audit.raw.json` — exit 0, one invocation, `PASS_METHOD_SCOPED`, errors `[]`.
- Auditor independently replayed 66 action-test transitions across nine cases; candidate-declared case deck and independent outputs agreed exactly.

## Results

- **Silent-effect alias:** six permitted length-1/2 test words had equal predictions, while independent safe-action profiles differed. Screenshot and last-one-observation baselines merge this pair; the oracle-informed latent baseline and full-history baseline keep it separate. The predictive candidate returned `HOLD_NOT_IDENTIFIABLE` and did not authorize merge.
- **Fresh independent receipt:** six bounded test words; the fresh receipt differs and keeps histories separate.
- **Null case:** six bounded test words; independent safe-action profiles and predictions match; predictive representation merges within the horizon while full-history equivalence remains conservative.
- **Delayed effect:** both permitted prefixes through horizon 2 match. A difference at step 3 is recorded as `UNKNOWN`; no unbounded-equivalence claim.
- **Controls:** forbidden write probe issued 0 times; stale and source-correlated receipts rejected; external generation mutation invalidates cached prediction; equal test vector does not certify cross-route hard-label equivalence.

## Environment / limits

Windows 11 x64 build 26200, CPython 3.12.10, standard library only. Docker was not used: Docker Engine timed out, the service is stopped, and no exclusive shared slot is assigned in #5085. No engine, image, container, GPU, WSL state, network, model, GUI, application, physical input, user data or external effect was touched.

This is a fixed deterministic synthetic finite deck, not learned PSR behavior. It does not establish test-vocabulary completeness or learnability, calibration from sparse traces, long-horizon behavior, real receipt independence, dynamic/nonstationary GUI coverage, action authority, route conformance, product safety, or live utility. The latent-state result is an oracle-informed comparator, not a candidate implementation. Preserve this scoped result without reclassifying earlier Issue evidence.

## Integrity

- `candidate.raw.json`: 8,043 bytes; SHA-256 `AA8C1DF2966BAB84D797030723A2A401FAD5DA2E71140A4958EAE2F7A6CD613E`.
- `audit.raw.json`: 198 bytes; SHA-256 `DAA18A101BE85EAE7F251CEB2BE6D16B899AC6230A895169135BE63C6D844879`.
- Source/freeze identities are in `FREEZE.json`; raw result hashes are in `SHA256SUMS`.
