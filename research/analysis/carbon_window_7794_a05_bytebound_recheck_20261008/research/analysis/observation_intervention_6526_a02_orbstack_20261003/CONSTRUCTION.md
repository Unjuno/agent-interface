# A02 construction and execution record

Allocation `OBSERVATION-INTERVENTION-6526-A02-ORBSTACK-20261003-01` is a
fresh successor. Predecessor A01 remains immutable at
[`observation_intervention_6526_a01_orbstack_20261003/FORMAL_FAILURE.md`](../observation_intervention_6526_a01_orbstack_20261003/FORMAL_FAILURE.md).
No A01 result rows are pooled or reused.

## Method correction and construction gates

- A01's auditor incorrectly treated `action_ns - trial_start_ns == 90 ms` as
  an integrity condition. Its timer was armed after per-trial observer setup;
  actual callback delay is part of event-loop observation intervention, not
  something to silently normalize away.
- A02 arms the identical `Tk.after(90, ...)` callback immediately after the
  trial start marker and *before* starting the observer thread. It records
  `action_schedule.scheduled_ns`, configured delay, and arm-to-trial-start
  offset. The preregistered offset integrity bound is 0–5 ms.
- Candidate lateness beyond the 100 ms sensitive deadline is an observed
  failure of the persisted effect at that deadline (if records/oracle remain
  complete), not automatically a method STOP. Early callbacks, invalid arm
  provenance, missing callbacks or corrupted receipts remain STOP gates.

Construction counts, smoke receipts, six-case raw logs, and audit:

| Gate | Status | Evidence |
|---|---|---|
| Xvfb/Tk/xwd smoke | PASS | `results/construction/xvfb-tk-smoke.json` |
| 6-case schedule-origin fixture | PASS, construction-only | `results/construction/audit.json` and `raw/` |
| local mutation/unit suite | PASS, 13/13 | command/result below |
| formal candidate/auditor | NOT STARTED | must follow a separate prospective freeze and Issue comment |

The smoke opened Tk 8.6.14 under private Xvfb; `xwd` returned 5,246,059
bytes (SHA-256 in the receipt). The six-case candidate exited 0. Its independent
construction-only audit found 6 starts/schedules/actions/deadlines, 28
screenshots, 52 sham ticks, zero screenshot errors, and zero integrity errors.
Arm offsets were 0.005917–0.020417 ms; callback delay from the recorded
`after(90)` schedule was 91.104–93.077 ms; all six effects were present at
their construction deadlines. These are readiness cases, not A02 scientific
rows.

Local command: `python3 -B -m unittest discover -s
research/analysis/observation_intervention_6526_a02_orbstack_20261003 -p
'test_*.py' -v`; 13/13 passed. Python `py_compile` also passed.

## Retained construction setup notes

The private VM `research-6526-observer-a01-20261003` and immutable image were
created for A01; no other VM is used or modified. Exact image identity and
A02 source/input hashes are in `FREEZE.json`. The VM container daemon is private
to this VM; formal containers used `--network=none --cpus=1 --memory=512m
--init --pull=never`. See [`FORMAL_REPORT.md`](FORMAL_REPORT.md) for the frozen
candidate and independent-audit outcome.
