# Issue #5962 — mission survival T0

## Result

**PASS_METHOD_SCOPED.** The exact finite model demonstrates that identical per-task success marginals do not determine continuous-session mission survival, and the direction of a route ordering depends on the declared terminal predicate. This is a mathematical/method control, not evidence about any Agent Interface route or real user session.

The candidate enumerated 1,530 complete binary paths: three stationary kernels × lengths 1–8 × every one of the `2^N` sequences. The independent auditor returned `PASS`, no errors, and rejected all five corruption controls (missing path, duplicate path, changed probability, erased censoring, and omission of a failed session from the denominator). It separately recalculated every rational path probability, each per-task failure marginal, all three unit probability masses for every N, endpoint/censoring fields, and the path maximum failure-run length; an absorbing-state dynamic program independently agreed with both mission-survival endpoints.

All kernels have `P(S at each task) = 4/5`. At N=8, exact mission-survival probabilities are:

| Kernel | No F anywhere | No adjacent FF burst |
|---|---:|---:|
| IID | 65536/390625 (0.16777216) | 304384/390625 (0.77922048) |
| Clustered failures | 893871739/1600000000 (0.558669837) | 4126411/6250000 (0.66022576) |
| Alternating failures | 2187/20480 (0.106787109375) | 1 (1.0) |

Thus the clustered kernel has greater survival than IID under the strict no-failure endpoint, but lower survival under the two-consecutive-failure endpoint. The alternating kernel never reaches an FF burst, yet performs poorly on the no-F endpoint. This illustrates why a mission contract must be specified before comparing routes; it does not show that real route failures have any of these kernels. The all-started-session denominator is retained even when a session terminates early; per-row suffixes after terminal failure are marked censored, not silently removed. Maximum failure-run summaries are over complete potential paths and are not claimed to be observable after an operational stop.

## Construction and execution record

Before source freeze, construction tests exposed two auditor defects (historical failure states were not absorbing in the independent endpoint oracle) and one ineffective corruption control (it altered a row with zero censored suffix). These were corrected before freeze. The final construction suite passed 4/4 and `py_compile` passed; final source SHA-256 identities are in `FREEZE.json`. These are pre-freeze construction findings, not scientific trial rows.

Frozen candidate command: `python candidate.py` (invoked once; exit 0), emitted `raw-candidate.json` with SHA-256 `15e1c649839961fda74319d7481772614bfa352ddcfe59216a03e10560ba2634`. For compact publication, the exact byte stream is retained as `raw-candidate.json.gz` (SHA-256 `8e139ae44cdc291fc5e857d9f556fbba0506b7ffd095ef26cadc8480df0fb94c`; 11,030 bytes); decompressing it reproduces the raw JSON digest. Frozen auditor command: `python auditor.py raw-candidate.json` (invoked once; exit 0), captured in `audit-result.json`, SHA-256 `320dafbb15bdbccdadd299e343b00c22b83a35f4ef7a40566302f58debd4fbc8`. No post-freeze candidate or auditor rerun occurred.

**Computer/resource record:** Python 3.12.10 on Windows, PowerShell 7.6.6, CPU-only, standard library. Docker CLI 28.5.1 and the Docker Desktop `desktop-linux` context were present; `docker info` did not return within approximately 15 seconds, so that read-only probe was interrupted and no container was started. No GPU, model, GUI, network, external data, or user data was used. There is no Docker image identity because the daemon did not respond and no image was pulled or run.

## H / T / D / C / U

- **H:** Equal per-task success marginals alone do not identify continuous-session survival or burst-risk ordering; dependence can change mission survival differently for different predeclared endpoints.
- **T:** Exact-enumerate all length-1..8 binary paths for IID, clustered-failure, and alternating-failure stationary kernels with common `P(F)=1/5`; score terminal failure on any F and on a consecutive FF pair; retain potential paths, operational observed prefixes, censored suffixes, and every initiated session in the denominator; compare with an independent rational auditor and absorbing-state DP.
- **D:** Pass method-scoped because all marginals and path masses reconcile exactly, both endpoints match the independent DP, every path/censoring/run-length field is validated, the N=8 endpoint rankings differ, failed sessions remain in the denominator, and all five mutation controls are effective and rejected.
- **C:** Kernels are selected synthetic controls, not fitted/observed route dynamics. Equal binary marginals omit task heterogeneity, resets, route assignment, state carryover, adaptive work, safety consequences, and uncertainty from finite empirical sessions.
- **U:** No real session linkage, route result, task family, agent behavior, production reliability, causal benefit, or runtime claim is established. T1 may audit retained session eligibility; T2 requires a distinct isolated live allocation, full session provenance, independent effect labels, and matched scoring. Do not multiply isolated-task marginals into mission survival without a justified dependence model.

## Reproduction

The construction checks are `python -m unittest -v`. To reconstruct the raw candidate bytes, decompress `raw-candidate.json.gz` to `raw-candidate.json`; verify its SHA-256 against the original-output digest recorded above. Then `python auditor.py raw-candidate.json` audits that retained artifact and does not regenerate the candidate paths. `SHA256SUMS` covers the published package files except itself.
