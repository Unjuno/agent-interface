# Representative native-suite WSL2 vs WSLc cost successor — #6389 A04

Status: preregistered, not run. A03's synthetic finite-trace result stays
unchanged. This allocation measures the project's actual 205-test local
runtime integration suite on one frozen source under native Ubuntu/WSL2 and
the existing WSLc suite image; it does not reuse A08's single-arm timings.

## H / T / D / C / U

- **H:** For this exact CPU-only contract suite, native Ubuntu/WSL2 preserves
  all test outcomes and reduces median end-to-end invocation time by at least
  10% versus WSLc.
- **T:** Three fresh sequential pairs, order native→WSLc, WSLc→native,
  native→WSLc. Each invocation runs the committed `runtime/integration_checks/native.py`
  suite once. Native uses one pinned Python venv for both suite groups; WSLc
  uses the pre-existing A08 suite image. Network disabled in WSLc, source and
  Git metadata read-only, unique output directories, one requested CPU, and
  512 MiB requested (not treated as enforced). The Windows host times the full
  CLI invocation. No retry.
- **D:** `PASS_COST_SCOPED` requires six clean exits, `result.json` PASS in each,
  matching protocol/harness test counts and runner identity across arms and
  repetitions, all raw log hashes valid, and native median at least 10% lower.
  Equivalent complete suite results without the cost threshold are
  `PASS_PORTABILITY_ONLY`; mismatched/failing tests are `FAIL`; a pre-candidate
  runtime/source/idle gate is `STOP`.
- **C:** Python patch and libc differ (Ubuntu Python 3.12.3 vs WSLc Python
  3.12.14); this suite is synthetic/inert contract coverage, not GUI use.
  WSLc has previously warned that cgroup/swap-limit capabilities are unavailable.
- **U:** No Docker comparison, peak-RSS attribution, hard memory-limit/OOM
  claim, GUI/model behavior, hosted Actions change, or repository-wide migration
  conclusion. Three pairs do not characterize fleet distributions.

The exact frozen base commit, image ID, commands, no-retry boundary, source
identities and output location are recorded in `FREEZE.json`. Formal outputs
remain outside the read-only checkout during measurement and are copied into
`formal/` only after the candidate sequence ends.
