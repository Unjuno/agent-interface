# Issue #6611 T0 result — 2026-10-02

Disposition: `METHOD_PASS_SCOPED`.

The frozen finite synthetic assay emitted 16 route-by-reader rows: two routes (`compact`, `portable`) across eight declared reader cases. The two routes met the same initial contract in all rows. The independent auditor reported all five controls true, zero errors, and retained the failed reader-open case as `UNKNOWN`. It detected silent formula loss, render-only degradation while the stored value remained correct, a missing external dependency, and a case where the faster compact route survived while the portable route did not. A metadata-order change and a cosmetic theme change preserved the declared significant properties.

Declared operation units are illustrative only: compact total cost 2 and portable total cost 4. They are not observed time or effort and do not establish a route recommendation. The transforms and property oracle are hand-authored finite fixtures, not real office-format semantics.

## Execution and evidence

- Frozen source commit: `d1e7948ad2d5d4f73d98df50f189a994dc02dac3` on `research/version-crossing-artifact-survival-6611-t0-20261002`; all five source blobs were read back and matched local Git blob IDs before formal execution.
- Candidate, separate WSLc invocation, exit 0: `wslc.exe run --pull never --rm --network none --cpus 0.25 --memory 256m --mount type=bind,source=<frozen-source>,target=/src,readonly --mount type=bind,source=<dedicated-results>,target=/out --workdir /src python:3.12-slim python -B candidate.py /src/fixture.json /out/candidate.json`.
- Independent auditor, separate WSLc invocation, exit 0: same container boundary with `python -B audit.py /src/fixture.json /out/candidate.json /out/audit.json`.
- Exact local SHA-256: `candidate.json` `ba966112da3033ceb95fdfe7e594cdf591fd13e71c766914bfe2b3a291f23967`; `audit.json` `48f954baefb8e5c6aefb11f291e04bc50a55e3d1320e843a9c8ca1c343a1fe1d`.
- Exact Git blob IDs after remote publication: raw `7697d5afb95a92d8347b794a7bf35220f663b0de`; audit `9af66dfbd5474892f5fd4ba0e8bf0df84539be62`.
- Image: `python:3.12-slim`, repo digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Python 3.12.14, linux/amd64. Network disabled; source mount read-only; output in dedicated writable directory.
- Both WSLc invocations warned that kernel swap-limit capabilities/cgroup are unavailable (`Memory limited without swap`). Memory-limit enforcement is not independently verified.
- Construction checks: `python -B -m unittest -v test_t0.py` — 6/6 passed before the formal allocation. Construction attempts are distinct from the single formal candidate and auditor invocations.

## Scope

This supports only sensitivity of a finite, hand-authored scorer to the declared transformations. It does not establish compatibility across real application versions, long-term preservation, format rankings, user preferences, actual repair cost, or product benefit. No real application, model, GUI, user artifact, or network access was used.
