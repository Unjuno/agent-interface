# Preregistration — Issue #6519 formal allocation 02 (T0b)

## Purpose and relationship to allocation 01

This is a fresh execution allocation for the unchanged, previously frozen T0 method. Allocation 01 (`AFFORDANCE-REGRESSION-6519-T0-20261002-01`) is terminal with `STOP_LAUNCH_PATH_UNRESOLVED`: a relative path failed before tests ran. That failure remains immutable and is not evidence for or against the method. T0b changes only the operational runner to derive absolute paths from its own script location and uses fresh output directories. The candidate, fixture, oracle, auditor, hypotheses, arms, invariants, decision gate, and formal budget are unchanged; no source is repaired or retried under allocation 01.

## Frozen method

The question, H/T/D/C/U, eight synthetic observations, four canonical arms, five planted corruption arms, 72-row candidate denominator, independent raw-only audit, and scoped interpretation are exactly those in the package-root `PREREGISTRATION.md` and `RUN_PROTOCOL.md`, frozen at `6147a501cd04710c306af7fa1535870b9cf25145`. The prior host-only protocol suite passed 12/12; it is construction evidence, not formal container evidence.

## T0b operational change and formal budget

Allocation ID: `AFFORDANCE-REGRESSION-6519-T0B-20261002-01`.

The only new executable is `runner.ps1` (SHA-256 `4da8efc734888112e5282d4f5d19d972404f4c3ef82c1201929dfbb735666e74`). It resolves package and mount paths from `$PSScriptRoot`, rejects relative/empty mounts and non-fresh outputs, records command/UTC times/exit code, and pins the invocation arguments below. Three host-only `-DryRun` checks resolved the expected absolute paths and distinct fresh outputs. These checks make no container calls.

Formal budget: construction=1, candidate=1, independent auditor=1, retries=0. Each stage has its own output directory under this allocation. A nonzero exit, missing/ambiguous artifact, hash mismatch, or failed gate consumes that stage and is recorded; no retry. Candidate source sees only the frozen candidate source and fixture. The independent auditor sees only its frozen source, fixture, oracle, and an unchanged copy of candidate raw output.

Pinned runtime: native WSLc CLI `wslc.exe` reports version `5.0.1.1` on the T0b host (the parent allocation's `3.0.1.0` runtime record is retained unchanged); image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (cached; amd64, Python 3.12.14 verified for this digest). No Podman or Docker CLI is used. Network disabled, 1 CPU, requested 1 GiB memory, UID 65534; no GPU is needed for this deterministic synthetic protocol test. The kernel emitted its recorded warning that swap-limit capabilities/cgroup are unavailable; memory is limited without swap and enforcement of the requested cap is not asserted. The exact command is built by `runner.ps1` for each stage; no image pull is permitted.

Latest fetched `origin/main` at T0b freeze: `211f74a8f242294eb60240b84d89fd48180709f6`. The branch merged this main head before freezing T0b. Main's intervening changes do not touch this experiment package. Branch head at the T0b preregistration commit is recorded by Git history.

## Fresh output paths and launch checks

- `construction/`
- `candidate_output/`
- `audit_input/`
- `audit_output/`

All four were empty at freeze. Absolute-path dry runs passed for construction, candidate, and auditor. Before formal construction: verify frozen/staged source hashes, branch/main collision state, cached image digest, empty construction output, and that WSLc has no unrelated active container. Then invoke the construction stage once. Candidate and auditor are eligible only after their respective gates pass.

## Source hashes

| File | SHA-256 |
|---|---|
| package `README.md` | `1d7ca1d9195a27690130af79271e99d49757678be0859a50229c2c34ed8ed6d1` |
| package `PREREGISTRATION.md` | `8f79bee1184b48e40c501ed0741bd6316edfae010a149d3ebe6675851998da04` |
| package `RUN_PROTOCOL.md` | `40648d1db63703e6980b34acb89f0350a9157cdadcd9f653deae39063525059a` |
| package `fixture.json` | `23fa159a1c8720f1c783d34bd0b26bf570d50628f04ae1cd4a34c22fb8d261ff` |
| package `oracle.json` | `16d3c3d967e1a22401594686ef07d646c94c4593b1e7d32df4c32f24f65bbb1f` |
| package `candidate.py` | `964926f73a9d5a2bbf1929ac26a87395dba5a96fe9ea3581f7d6c62b36e202bb` |
| package `auditor.py` | `8dc5eb835970e433579ae9d7e9e488f367566243e2cc7dfea9d8bc168d8f8a80` |
| package `test_protocol.py` | `513c9bfb5e4cfba7e6b4431b305aa1ddc3546fe2390f06da5836262a6adc40c6` |
| staged candidate.py | `964926f73a9d5a2bbf1929ac26a87395dba5a96fe9ea3581f7d6c62b36e202bb` |
| staged candidate fixture | `23fa159a1c8720f1c783d34bd0b26bf570d50628f04ae1cd4a34c22fb8d261ff` |
| staged auditor.py | `8dc5eb835970e433579ae9d7e9e488f367566243e2cc7dfea9d8bc168d8f8a80` |
| staged auditor fixture | `23fa159a1c8720f1c783d34bd0b26bf570d50628f04ae1cd4a34c22fb8d261ff` |
| staged auditor oracle | `16d3c3d967e1a22401594686ef07d646c94c4593b1e7d32df4c32f24f65bbb1f` |
| runner.ps1 | `4da8efc734888112e5282d4f5d19d972404f4c3ef82c1201929dfbb735666e74` |

At preregistration: formal construction attempts=0, candidate invocations=0, auditor invocations=0, retries=0.
