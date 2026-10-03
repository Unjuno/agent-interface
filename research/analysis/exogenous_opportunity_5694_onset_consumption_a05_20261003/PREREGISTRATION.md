# A05 preregistration — onset consumption in matched synthetic timing

Issue: #6967. Predecessor: #6803 / PR #6805. No predecessor output or disposition is changed.

## H / T / D / C / U

- H: With identical capture schedule [10, 50] ms, expiry 20 ms, horizon 60 ms and all other input fields held fixed, moving onset from 9 to 11 ms changes the first capture inside the cue interval from 10 ms to none. The candidate must consume onset and capture timestamps; a fixture-provided membership label cannot supply the answer.
- T: One finite standard-library fixture, one candidate invocation, one independent raw-only auditor invocation, no retries. The candidate receives fixture.json only; oracle.json is passed only to the auditor. The nine cases comprise the matched phase pair, delivery-after-expiry, no decision, no effect, safe stop, unsynchronized clock, right censoring and no opportunity. Candidate output includes first_acquisition_capture_ms. Five frozen data mutations exercise audit rejection.
- D: PASS_METHOD_SCOPED only when the c01/c02 pair differs only in onset, candidate reports 10/null respectively, all nine output rows match oracle.json, audit independently reconstructs all rows with no errors and rejects 5/5 mutations, and all construction tests pass. Otherwise retain FAIL_METHOD or STOP by cause.
- C: Cue intervals, event times and outcomes are authored synthetic values. The test establishes a finite measurement contract, not real timing prevalence or capture-system performance.
- U: No live GUI, model, user data, OS input, external effects, GPU/CUDA, safety-rate, human-tempo or product claim.

## Runtime and one-shot boundary

WSLc 3.0.1.0; Python 3.12.14 image ID sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4, repo digest python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f. Verify image identity locally; --pull never. Linux/amd64, --network none, --cpus 0.25, --memory 512m, --user 65534:65534, source read-only, separate fresh output directories. No GPU.

Candidate command:
python -B /src/candidate.py --fixture /src/fixture.json --out /out/candidate.raw.json

Auditor command:
python -B /src/auditor.py --fixture /src/fixture.json --oracle /src/oracle.json --raw /results/candidate.raw.json --out /out/audit.json

Before formal execution: refresh current main and all relevant issues/PRs/branches; compare the exact current main to source freeze and resolve any A05-path overlap; verify no active overlapping WSLc container; confirm pinned image digest; confirm candidate/audit outputs absent; record runtime warning. Candidate max 1, auditor max 1, retries 0. If any precondition or construction test fails, STOP before candidate invocation. If candidate exits nonzero, preserve the first output and do not invoke auditor or retry.
