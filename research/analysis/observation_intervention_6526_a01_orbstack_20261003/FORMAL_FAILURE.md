# Issue #6526 A01 formal allocation — STOP

Allocation `OBSERVATION-INTERVENTION-6526-A01-ORBSTACK-20261003-01` was
executed once under the prospective freeze. It is classified
`STOP_AUDIT_ERRORS`. This is a method failure, not support for or against the
observation-intervention hypothesis. Do not use, repair, or replace these
rows as a successful experiment.

## Execution and audit

- Candidate: one container invocation, exit 0, receipt reports 180 trials.
- Independent auditor: one read-only container invocation on recovered raw
  output, `STOP_AUDIT_ERRORS`.
- All 180 trial starts, action events, deadline files, and effect files were
  present. Container limits were network `none`, 1 CPU, 512 MiB; cgroups
  reported `cpu.max=100000 100000` and `memory.max=536870912`.
- Auditor found `action-delay-mismatch` for all 180 trials and correctly
  withheld rates, paired tests, and any H classification.
- Out-of-band diagnostic of raw timestamps: action-start minus trial-start
  ranged 90.212–95.462 ms (median 92.026 ms). The fixture starts the Tk
  90-ms timer after observer setup and other per-trial work, whereas the
  auditor incorrectly compared its timestamp with the earlier `trial_start`.
  The preregistered exact-equality gate was therefore not met. No post-hoc
  tolerance, code change, or rerun is allowed for this allocation.
- The candidate's 90-ms Tk callback setting was fixed across conditions, but
  this does not rescue the failed event-timing provenance gate. Statistical
  outcome rates remain intentionally unreported.

## Preserved evidence

`results/formal-a01/raw/` contains the recovered candidate output, including
`app-events.jsonl`, 180 deadline snapshots, effects, candidate receipt, and
Xvfb stderr. `results/formal-a01/independent-audit.json` is the sole auditor
result. `FREEZE.json` and `formal-trials.json` bind the prospective inputs.
`CONSTRUCTION.md` retains setup/build failures and their bounded repairs.

## Follow-up boundary

Any further test must be a separately numbered successor allocation and
separate additive path. First fix the schedule-origin contract (record the
actual callback target/origin or define and validate a prospective tolerance),
retest with new construction-only fixtures and mutations, then prospectively
register a new seed and full decision rule on Issue #6526. This A01 STOP and
its raw data remain immutable historical evidence.
