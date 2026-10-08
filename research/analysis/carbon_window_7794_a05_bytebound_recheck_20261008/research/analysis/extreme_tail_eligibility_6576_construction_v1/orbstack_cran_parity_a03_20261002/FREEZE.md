# A03 freeze (before candidate invocation)

Experiment: Issue #6576, pinned CRAN TailID R versus the repository's Python
upper-tail equivalent. This is implementation-parity evidence only and does
not touch the formal six-case T0 allocation.

## H / T / D / C / U

- **H:** On six byte-identical, seeded 400-observation stationary exponential
  samples, the Python upper-tail TailID equivalent will reproduce CRAN TailID
  1.0.0 candidate indices, sequential sensitive indices, and `ismev` 1.43 GPD
  MLE/shape-confidence-interval states within the preregistered tolerances.
- **T:** Run the original TailID R functions and the existing Python port once
  each, in network-disabled containers, on the frozen files under `input/`.
  R uses R 4.4.3, `ismev` 1.43 and `jsonlite` 2.0.0; Python uses CPython
  3.12.15. An independent Python auditor consumes only the two raw outputs,
  preregistration and frozen samples. Candidate invocation count: one; audit
  invocation count: one only if both candidate arms exit 0; retries: zero.
- **D:** PASS only if every R fit converges, the R/Python candidate indices and
  sensitive indices match exactly, thresholds agree within 1e-10, MLE scale
  relative error is <=1e-5, and shape/CI absolute errors are <=1e-5 for all
  compared states. Any mismatch is retained as FAIL/INCONCLUSIVE, never
  repaired by rerunning.
- **C:** Six small synthetic samples test a narrow upper-tail implementation
  path. They do not establish statistical performance, a better estimator,
  TailID package namespace behavior, or stability across distributions,
  versions, platforms, ties, larger samples or malformed data.
- **U:** No physical release timing, causal mechanism, safety deadline,
  production workload, worst-case bound, calibration superiority or formal
  #6576 T0 result is tested.

## Frozen environment

- OrbStack VM: `agent-interface-6576-tailid-parity-a03-20261002`, Ubuntu
  24.04.5 arm64, VM ID `01M3Y3Z0A534XSFW13KW95E98Y`, 2 CPU / 4 GiB, isolated
  and isolate-network enabled.
- Dedicated Docker Engine: 29.1.3 linux/arm64, daemon ID
  `2cc9fcfe-a017-4956-959f-0b1a85657dde`; no shared OrbStack Docker context.
- R base: `rocker/r-ver:4.4.3` digest
  `sha256:3dae5d2eeddf74f10e0a81fb6b7ae350295e288000304f438b844b2c1e00fe2c`;
  prepared R image ID `sha256:99bc0ddb9a9fc3a6888e80fa1186a431d70c69df42707acfba2bdc9915204a2c`.
  Installed versions: R 4.4.3, ismev 1.43, jsonlite 2.0.0, mgcv 1.9.1.
- Python image: `python:3.12-slim` digest
  `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`;
  CPython 3.12.15 linux/arm64.
- Candidate containers: `--pull=never --network=none --read-only`, writable
  `/tmp` only, 1 CPU / 2 GiB / swap 0, read-only inputs and source, dedicated
  writable output mount. Preflight observed `cpu.max=100000 100000`,
  `memory.max=2147483648`, `memory.swap.max=0`.
- ismev source archive `upstream/ismev_1.43.tar.gz`, SHA-256
  `b2b7ddaed7994a4efd92a215ba90da7bdb63ccdcc3ebd26ffd4f476211e9c336`;
  its `R/gpd.R` SHA-256 equals the fixed GitHub commit
  `25223b17285d45bf3911efd79ac75f363e7ae495` blob content SHA-256
  `0325c32dd518f59ad0d8f7e5473939f4660ac62eb75a73443ada08d67e5916af`.
- TailID source: CRAN TailID 1.0.0 commit
  `f99b10ff27f37ac62ba1d44ce79b4fc886f72997`, tree
  `41e9b3e805b42face93fb08ae7f4169e361f8bf1`. The four used R files and their
  Git blob IDs are retained under `upstream/tailid_R/`; their SHA-256 values
  appear in `SHA256SUMS`.

## Frozen input and code hashes

Preregistration SHA-256:
`8b782ccb9fe281e49fa994e681b1381b9f309925e4a8adf9fb15af6dd9cbff46`.

Candidate harness SHA-256 values:

- R: `292fc27674058d5cc585b6ef55933723bbf9937e732ee6430007b4ba18a9f898`
- Python: `bf0001f6d709bdf8919f20bb7e7c3a69fbe8f39d381874257af9c728b16140cc`
- Python TailID port: `1931b354fedb3db2a5cda9c52cdd4c1e9002bb04dbe952980704c282777a63c4`
- Fixture generator: `19f872e74fd413c22658dddbee6a6d5fb675b952496ffd72f00f3bebb9682a7e`
- Auditor: `ffbb21928e81893498495d736e1b19272e01d6fe4fb66ba3d1579f9af0cd2389`

Each of the six exact sample files has its SHA-256 recorded in
`input/` and `SHA256SUMS`. The files were generated once with the frozen R
image and are mounted read-only in both candidate containers.

## Frozen acceptance and disposition

The machine-readable parameters are in
`crAn_parity_a03_prereg.json` (same preregistration hash above). Source,
sample, candidate, and image identities are not to be changed after this
freeze. A candidate crash, nonzero status or any parity mismatch is the
result; do not retry or patch in-place.
