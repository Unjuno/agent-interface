# #6613 EDF deadline successor A01 result

**Disposition: `FAIL_HYPOTHESIS` (finite synthetic scope).** The candidate and
independent raw-only auditor each ran once and exited 0. The auditor exactly
replayed all 360 policy-trace rows (`PASS_RAW_REPLAY`) and rejected all five
planted raw mutations. No retry or tuning occurred.

## H / T / D / C / U

- **H:** EDF was expected to improve on-time optional completions versus FIFO
  and shortest-service-first by at least 0.5 per trace in the
  `asymmetric_deadlines` stratum, while remaining within a 0.5-per-trace
  noninferiority bound to FIFO in the other strata and meeting eligibility and
  mandatory-event gates.
- **T:** 40 new seeds (20000–20039) × 3 strata × 3 policies = 360 rows; integer
  ticks, one nonpreemptive server, 12 optional tasks per trace, and one
  mandatory event in `revocation_mandatory`. Candidate/auditor ran in WSL2
  Arch Linux with Python 3.14.7. No GPU/CUDA/model/GUI/network/container was
  used.
- **D:** Exact replay and all integrity/safety controls passed, but the
  preregistered performance hypothesis failed. Asymmetric mean on-time optional
  completions per trace: EDF **1.80**, FIFO **2.65**, shortest-service **4.95**.
  EDF deltas were −0.85 vs FIFO and −3.15 vs shortest-service, opposite the
  required ≥+0.5 gains. Burst/recovery: EDF 1.025 vs FIFO 1.70 (−0.675), also
  below the −0.5 noninferiority floor. Revocation/mandatory: EDF 2.60 vs FIFO
  3.10 (−0.50), at the bound. Mandatory events completed in all revocation
  traces; no hard-eligibility dispatch or accounting mismatch was found.
- **C:** EDF's urgency order can sacrifice jobs with longer slack; with
  nonpreemptive variable service, shortest-service-first substantially
  outperformed EDF on this authored finite fixture. These outcomes depend on
  the chosen arrival, deadline and eligibility distributions.
- **U:** No people, live GUI, actual authorization, real service-time or
  deadline distribution, deployed fairness, operational safety, or product
  benefit was measured. The result does not justify any real scheduler change.

The prior service-debt A01 result remains `FAIL_HYPOTHESIS` and is not edited.
This distinct EDF successor also failed; stop both policy paths here. No new
threshold, seed, or policy run is authorized by these results.

## Execution and immutable evidence

Current-main base at freeze: `6fdfa6b2e2bbb13a58a235dae5499676d7dd417f`.
Frozen branch: `research/service-fairness-6613-edf-a01-20261003`; formal
allocation: `SERVICE-FAIRNESS-6613-EDF-A01-20261003`. The full allocation,
source/input hashes, exact environment and decision rules are in `FREEZE.json`
and `PROTOCOL.md`; exact invocation receipts are in `RUN_RECORD.json`.

- Candidate raw: 791,364 bytes, SHA-256
  `f2debd9597ed9e7fca79f614600263d0aa66428c1cf0175c84eaa71611be66ec`.
- Independent audit JSON: SHA-256
  `25faf56d693f2b6fe6d2e22a4c5db1649e529c94e05fda0351eb718fd273c5b1`.
- Five corruption controls rejected: duplicate row, forged seed, changed start
  tick, omitted mandatory release, and forged fixture hash.
- The auditor's equality check covers all 360 schedule rows and independently
  derives the reported metrics/disposition from those replayed rows. It does
  not assert the candidate's redundant `preregistered_summary` envelope; this
  metadata limitation is retained rather than repaired or rerun post-outcome.
- One pre-auditor shell precheck was mistakenly run from the repository root
  and exited before starting the auditor because its relative raw path was not
  present there. The corrected absolute-Windows/WSL invocation then ran the
  auditor once. No candidate or auditor result was overwritten.

Both outputs are retained unchanged. The historical result is synthetic and
method-scoped only; it has not been promoted to a human or product claim.
