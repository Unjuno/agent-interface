# Formal run record — Issue #8526 T0 A01

## Frozen allocation

- Run ID: `8526-path-readset-t0-a01-20261008`.
- Base: GitHub `main` commit `3f026dc67d745d7cc67f7cc09f250cb60d71f872`.
- Frozen protocol: `PROTOCOL.md`; exact pre-run source digests and command strings: `FREEZE.json`.
- Candidate environment: Windows 11 `10.0.26200-SP0`, AMD64, CPython `3.12.10`.
- Candidate source SHA-256: `F82BD377EF8925A8F9668BCCF2C5ECFF4970BAC71469228A19D5554288F79CBE`.
- Independent auditor source SHA-256: `DFF580D51689DC5353CF1915EFA949DFFA65734A00919E3123986A53A07CD1DB`.
- Pre-freeze construction suite: 9 passed, 0 failed. Formal calls during construction: candidate 0, auditor 0.

## Invocation custody

1. Verified all five frozen source hashes against `FREEZE.json`; all matched.
2. Candidate command: `python -B candidate.py --output results/candidate.json` — invoked once, exit 0, emitted `candidate_rows=39`.
3. Independent audit command: `python -B audit.py --candidate results/candidate.json --output results/audit.json` — invoked once after candidate success, exit 0.
4. Retries, replacements, post-freeze source changes, WSLc calls and Docker calls: 0.

The raw 39-row candidate output is preserved at `results/candidate.json`; the exact auditor output is at `results/audit.json`. Both output paths were exclusive-create.

## Observed audited result

`PASS_PATH_CONDITIONED_READSET_SCOPED`: 39 rows; two safe salvages over `GLOBAL_UNION`; false accepts `GLOBAL_UNION=0`, `EXECUTED_PATH=1`, `PATH_CERTIFICATE=0`; false invalidations `GLOBAL_UNION=2`, `EXECUTED_PATH=0`, `PATH_CERTIFICATE=0`; three certificate mutations rejected.

The one `EXECUTED_PATH` false accept is the incomplete hidden-read case. The certificate policy rejected it because dependency completeness was false. Both global-union and certificate policies refused that same incomplete instrumentation. The two salvaged cases changed/unknowned only the unexecuted branch input while retaining the same branch, active leaf, epochs, generation and deadline.

## Environment boundary

The experiment ran as native Windows CPython because it is a deterministic in-memory fixture with no GUI, model, network or OS-observation input and requires no container boundary. The shared WSLc lane remains gated by unresolved ownership in #7924/#8503; this run did not use or clear that lane. No Docker Engine/Desktop availability or comparison is claimed. This is not a Linux/container-portability result.
