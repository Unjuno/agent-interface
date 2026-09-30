# Issue #5315 — calibration-byte binding successor T0

**Scoped T0 result: PASS. Issue-level conclusion remains HOLD.** This finite
synthetic experiment repairs the specific v1 defect: the checker now hashes
the retained calibration bytes and verifies that declared counts match those
bytes. It does not implement SCRC and does not establish selective singleton
risk control for real workloads.

## H / T / D outcome

- **H:** For this synthetic fixture, a changed calibration digest/byte stream
  or inconsistent aggregate statistics must be rejected; ordinary CRC may
  only make the declared marginal claim; shift/mismatch must fail closed.
- **T:** One frozen deterministic run, 199 explicit binary calibration rows
  (8 errors), five evaluation arms, six negative controls. Frozen main
  `57b56de2831204885c55375737580e5d82d3ab98`; source refreeze commit
  `e4ce0d85a1d27b4ba9ea147413cfc2de468afaa1`. See `FREEZE.json`.
- **D:** All scoped gates pass: digest/rows/counts agree; corruption controls
  reject 6/6; marginal CRC upper is 0.045 <= 0.05 while the IID fixture has
  population loss 0.04 and selected conditional risk 1.00; the checker rejects
  conditional-risk scope; all four non-IID/mismatched arms return UNCERTAIN;
  no authority is granted.
- **C:** standard-library-only, 199 calibration records + 5 x 1,000 declared
  fixture rows, no stochastic sampling. Host-only because the shared
  Docker/CPU coordination Issue #5085 has not assigned this task a slot.
- **U:** The records and shifts are synthetic and fully specified. A hash
  authenticates neither author nor population; this is not a representative
  calibration cohort. This checks a supplied CRC summary/formula, not an
  implemented threshold-search/calibration procedure. No SCRC algorithm,
  shift detector, task-effect,
  model/GUI/runtime, production safety, or causal guarantee was tested.

## Observed values

| Arm | Contract decision | Marginal fixture loss | Selected conditional risk |
|---|---|---:|---:|
| IID reference | `ALLOW_MARGINAL_CLAIM_ONLY` | 0.04 | 1.00 |
| Temporal shift / stale | `REJECT_STALE` | 0.10 | 1.00 |
| UI/layout shift | `REJECT_POPULATION_MISMATCH` | 0.12 | 0.80 |
| Task-family shift | `REJECT_POPULATION_MISMATCH` | 0.10 | 0.50 |
| Adaptive repeated query | `REJECT_ASSUMPTION_INVALID` | 0.04 | 0.80 |

The IID result is the critical boundary: marginal loss below alpha does not
make the selected singleton group safe. The candidate therefore emits no
conditional certificate and maps singleton output to UNCERTAIN; `{PASS,FAIL}`
is retained as a descriptive set, not an action grant.

## Execution and validation

Exact formal command: `python3 -B run.py --out evidence/formal01/RESULT.json`
(exit 0; raw SHA-256
`7fcf41620c4423eef7c764f17a2a6e5a57d2ffe5e29d4b58693abe571783a26e`).
The separate auditor imports neither candidate nor runner and passed; audit
SHA-256 is `31bc562fd4dbc1a67f402f27efc717e15cbb6bf04f29eb32f35240481b93afb6`.
Four contract tests passed; `py_compile`, pre-run source/main/hash preflight,
and `git diff --check` passed. No container, network call from the runner,
package install, model, GPU, or GUI was used.

V1 remains immutable as a negative result: its non-empty digest mutation was
accepted. V2 is a distinct additive follow-up; no v1 raw or the parallel
split-conformal allocation in `research/analysis/` was modified or reused.

## Literature boundary

Classic CRC controls expected bounded monotone-loss risk under its stated
exchangeability conditions; it is not a conditional selective-risk theorem.
The selective conformal paper uses a distinct symmetric selection and
conditional-exchangeability construction. This T0 tests the interface's
scope-boundary handling, not that selective algorithm. Sources: [Conformal
Risk Control](https://arxiv.org/abs/2208.02814) and [Selective Conformal Risk
Control](https://arxiv.org/abs/2512.12844).
