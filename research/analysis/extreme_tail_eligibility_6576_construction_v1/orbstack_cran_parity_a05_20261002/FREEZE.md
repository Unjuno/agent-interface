# A05 preregistration and run freeze

Fresh-seed successor to the two preserved harness/auditor failures A03/A04.
It corrects the R `seed_list` adapter, scalar/list comparison, audit diagnostic
field handling, and cumulative Python step-trace. It does not reuse prior raw
outputs as A05 evidence.

## H / T / D / C / U

- **H:** Python's upper-tail TailID equivalent reproduces CRAN TailID 1.0.0
  candidate order, exact sensitive-index set and cumulative MLE/CI states on
  six byte-identical stationary exponential samples.
- **T:** Generate 6 x 400 observations in frozen R 4.4.3; run pinned CRAN R
  source and Python port once each in isolated network-disabled containers;
  run one independent raw-only audit only when both candidate arms succeed.
  Retries: zero.
- **D:** Exact candidate indices and order; exact sensitive-index set;
  threshold absolute error <=1e-10; scale relative error <=0.001; shape
  absolute error <=0.001; CI endpoint absolute error <=0.002; all R fits
  converge. Any missed criterion is retained as a failed parity result.
- **C:** Tolerances reflect valid A04 baseline cross-optimizer differences
  (max relative scale 1.43e-4, max absolute shape 1.47e-4, max CI endpoint
  2.39e-4); the limits give numerical margin, not statistical confidence.
  Six small synthetic samples do not establish calibration, superiority,
  package namespace behavior, cross-platform stability, physical validity,
  safety, or worst-case behavior.
- **U:** No formal six-case #6576 T0, physical input-release timing,
  production workload, causal dependence mechanism, or safety deadline is
  tested.

## Environment

Dedicated isolated OrbStack VM `agent-interface-6576-tailid-parity-a03-20261002`
(machine ID `01M3Y3Z0A534XSFW13KW95E98Y`, 2 CPU/4 GiB) and private Docker
Engine 29.1.3 (`2cc9fcfe-a017-4956-959f-0b1a85657dde`). R image
`sha256:99bc0ddb9a9fc3a6888e80fa1186a431d70c69df42707acfba2bdc9915204a2c`
(R 4.4.3, ismev 1.43, jsonlite 2.0.0, mgcv 1.9.1). Python image
`sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`
(CPython 3.12.15 arm64). Containers use network none, read-only root and
inputs, 1 CPU, 2 GiB memory, swap 0, with only a dedicated output mount
writable. Source and the ismev package archive are exact copies of A03 inputs;
their SHA-256 manifests are retained here.

## Frozen input/code and one-shot rule

Preregistration: `crAn_parity_a05_prereg.json`; six fresh sample files are in
`input/`. All R, Python, source, image, and input hashes are in
`SHA256SUMS`. Candidate invocation once; independent auditor once only if both
candidate arms exit 0; no retries, no in-place fixes after invocation.
Formal #6576 T0 allocation is separate and remains untouched.
