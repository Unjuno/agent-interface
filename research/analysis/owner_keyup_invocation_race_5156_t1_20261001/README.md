# #5156 T1 — concurrent one-shot reservation boundary

## H / T / D / C / U

- **H:** `invoke_allocation.run_one_shot` has a check-then-write gap: two callers
  that both pass the no-marker gate can both invoke the candidate. Creating an
  exclusive claim file before gate evaluation should admit at most one caller.
- **T:** In one bounded host-only runner, synchronize two threads after both
  baseline gate checks and dispatch them to one temporary results directory;
  compare with two simultaneous callers contending on a Windows filesystem
  `O_CREAT | O_EXCL` reservation. Candidate/auditor callbacks are inert counters.
- **D:** Reproduction requires two baseline candidate/audit callbacks. The
  reservation control passes only with one candidate, one audit, and statuses
  `[0, 2]`. Independently verify result counts, scope, and exact source hashes.
- **C:** This is a deterministic same-process thread schedule over a local temp
  directory. It is not a multi-process or multi-host stress test, and does not
  establish network-filesystem semantics.
- **U:** No Docker, X11, model, game, or formal #5156 input was invoked. The
  atomic-claim wrapper is a host-side construction proposal, not integrated
  production behavior and not evidence of key-up, occupancy, useful feedback,
  recovery, MAP01, or product reliability.

The source under Allocation 06 remains frozen and its STOP remains unchanged.
The experiment imports it read-only. A permanent claim intentionally fails
closed after a crash; that availability cost is not measured here.

## Execution record

Candidate command: `python run_experiment.py results/raw.json` (one invocation).
Independent audit command: `python audit_race.py results/raw.json results/audit.json`
(one invocation only if the candidate runner exits 0). Focused tests:
`python -m unittest -v test_race_guard.py test_audit_race.py`.

This package records a distinct host construction experiment while formal
Allocation 07 remains only a queue request without an exact resource grant.

## T1 result

`PASS_HOST_ONLY_RACE_BOUNDARY` for the declared same-process thread schedule.
The baseline deterministically invoked two candidate callbacks and two audit
callbacks after both threads passed the no-marker check (`[0, 0]`). With the
exclusive claim wrapper, exactly one candidate and one audit callback ran and
the other caller was refused (`[0, 2]`). The separate auditor returned no
errors. Raw record: `results/raw.json`; audit: `results/audit.json`.

The result validates a concrete check-then-write race in this host guard under
the forced schedule and a local NTFS exclusive-file-creation mitigation. It
does not verify contention between separate processes/hosts or network file
systems, and the wrapper is not integrated into a formal launcher.
