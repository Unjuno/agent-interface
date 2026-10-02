# A04 preregistration and run freeze

Successor to the harness-failed A03; A03 remains unchanged. A04 fixes only
the input-shape mismatch by iterating the frozen `seed_list` directly. It uses
six new seeds and a new output path. No prior A03 result is reused as evidence.

## H / T / D / C / U

- **H:** On six byte-identical, seeded 400-observation stationary exponential
  samples, Python's upper-tail TailID equivalent reproduces CRAN TailID 1.0.0
  candidate indices, sequential sensitive indices, and `ismev` 1.43 GPD
  MLE/shape-CI states within preregistered tolerances.
- **T:** Generate six samples once with frozen R 4.4.3; run original TailID R
  functions and the existing Python port once each in network-disabled Docker
  containers; then run one independent raw-only auditor if both arms exit 0.
  Retry count is zero.
- **D:** Require exact candidate and sensitive-index equality; threshold
  absolute error <=1e-10; scale relative error <=1e-5; shape and CI absolute
  error <=1e-5; every R fit convergence code 0. Any mismatch is retained.
- **C:** Six small synthetic samples test only a narrow upper-tail
  implementation path; no performance, superiority, safety, physical timing,
  arbitrary distribution, package namespace, cross-platform, or worst-case
  claim follows.
- **U:** No physical input-release endpoint, production workload, causal
  mechanism, safety deadline, calibration superiority, or formal #6576 T0 is
  tested.

## Environment and provenance

Dedicated isolated OrbStack VM `agent-interface-6576-tailid-parity-a03-20261002`
(Ubuntu 24.04.5 arm64, 2 CPU/4 GiB; machine ID
`01M3Y3Z0A534XSFW13KW95E98Y`) and its private Docker Engine 29.1.3
(`2cc9fcfe-a017-4956-959f-0b1a85657dde`). R image ID:
`sha256:99bc0ddb9a9fc3a6888e80fa1186a431d70c69df42707acfba2bdc9915204a2c`
(R 4.4.3, ismev 1.43, jsonlite 2.0.0, mgcv 1.9.1). Python image digest:
`sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`
(CPython 3.12.15, arm64). Each candidate container uses network none,
read-only root and inputs, 1 CPU, 2 GiB memory, swap 0, and a distinct writable
output mount. Preflight observed CPU quota `100000 100000`, memory `2147483648`,
swap `0` in each runtime. Fixed TailID and ismev source and the ismev source
archive are copied from A03 unchanged and independently hash-checked.

## Frozen inputs and code

Preregistration: `crAn_parity_a04_prereg.json`; samples are under `input/`.
Candidate harnesses are `crAn_parity_a04.R` and `crAn_parity_a04_candidate.py`;
Python TailID source is `tailid_equivalent.py`. Auditor is
`crAn_parity_a04_audit.py`. All hashes are listed in `SHA256SUMS`.

Candidate invocation once; auditor invocation once only if both candidate
arms exit 0; no retries and no post-invocation code edits. Formal allocation
and the six-case T0 remain separate and untouched.
