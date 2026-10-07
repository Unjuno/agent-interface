# A03 report

Status: construction checks complete; formal run not yet started.

## Construction evidence

Pinned network-disabled container, read-only source and isolated writable temp:

- `python -B -m unittest -v test_t0_a03`
- Result: PASS, 3 test methods; 16 independent corruption mutations rejected;
  valid corpus accepted; candidate and auditor overwrite refusals checked.
- An initial test attempt with a fully read-only container had no writable
  temporary directory and stopped before tests executed. No repository files
  were written by that attempt. The test was rerun with `/tmp` as the only
  writable mount and passed.

This is construction evidence, not the formal candidate/auditor result.
Formal run outputs, exit codes, raw and audit hashes, and exact container
settings will be appended after the one-shot execution.

## H/T/D/C/U

- H: see package README; current-source-grounded answers and UNKNOWN remain
  invariant across matched history arms.
- T: 48 matched synthetic rows plus two byte-offset controls; independent
  exact-schema and exact-byte auditor.
- D: synthetic only; formal outputs pending.
- C: candidate once, followed by auditor once only after candidate success;
  auditor must report PASS/48/2. Otherwise preserve FAIL/STOP.
- U: no live/model/task/latency/GUI/generalization inference.
