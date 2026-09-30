# Issue #5531 T4 successor — corrected-metric calibration

## Result

**PASS_SYNTHETIC_DELAY_CORRELATION_METHOD_SCOPED.** The corrected, pre-frozen raw-only auditor exactly reconstructed the successor runner's summaries and hash chains; audit `errors=[]`, `integrity_pass=true`. This result belongs only to allocation `fd5531-delay-correlation-20261001-02`. It does not validate or replace predecessor allocation `-01`, whose `STOP_AUDIT_REPLAY_MISMATCH` remains immutable.

## H / T / D / C / U

- **H:** Supported only under the frozen synthetic timing/witness generator. At primary threshold 4, typed suspicion lowered false final failures for healthy-heavy-tail episodes to 4/10,000 versus 2,120/10,000 for timeout-as-failure, while 8,994/10,000 crashed episodes reached FAILED by tick 8. This retains 1,006/10,000 crashes in SUSPECTED_UNAVAILABLE at the horizon, an explicit incompleteness cost.
- **T:** Five scenario classes; 10,000 fixed-seed episodes/class; thresholds 2, 4, 8; two policies; 300,000 policy rows. New seed range starts at 55,370,000 and does not overlap predecessor seeds. Three frozen deterministic probes exercised late-response rejection after terminal failure, stale/invalid decoys, and explicit restart plus current response.
- **D:** PASS for all frozen scoped gates: exact raw replay/hash chains; crash-by-8 8,994 >= 8,900; heavy-tail typed false terminal episodes 4 <= 10 and below baseline 2,120; deterministic boundary probes matched; decoy accounting matched; independent auditor returned no errors.
- **C:** A simple timeout remains cheaper when a false terminal classification is preferable to delayed progress. The typed policy's long suspicion holds (e.g. 55,096 aggregate ticks in partition/recovery; 31,066 in crash episodes) are not free.
- **U:** Synthetic discrete delays and hand-set witness probabilities only. No real heartbeat, OS failure, observer independence, GUI, authority, task completion, safety guarantee, SLO, or deployment threshold is established. Correlated/nonstationary/malicious witnesses are uncalibrated.

## Provenance and execution

- Frozen main: `29861fa860ad48bc47af68f2ebf330b1f5c9d842`.
- Construction-02: 8/8 tests passed before freeze; auditor AST parse passed. Construction-01's seed-overlap finding is retained separately and was not formal.
- Runner: exactly one invocation, exit 0, host CPython 3.11.9 / win32, `python -B`, exact GitHub-readback source streamed in memory.
- Auditor: exactly one invocation, exit 0, 300,000 policy rows recomputed, candidate not imported.
- Exact source blobs, raw/audit SHA-256 and Git blob identities: `FREEZE.md` and `FORMAL-01.json`.
- No retry, tuning, or replacement. Predecessor result preserved unchanged.

This used local CPU only. Docker/OrbStack was not used because the current #5085 lease belongs to a different allocation. LM Studio/model inference and GPU computation were not needed; no network experiment, GUI, OS input, or effectful action occurred.
