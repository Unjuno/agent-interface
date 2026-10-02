# Matched-run boundary spectra — Issue #6640 T1

Frozen hypotheses, experiment, decision rule, scope, and allocation are in [`PROTOCOL.md`](PROTOCOL.md).

## Construction / formal separation

`make_fixture.py` creates the exact fixture and hidden oracle. `candidate.py` never reads `oracle.json`. `auditor.py` independently reconstructs every ranking, row/seed denominator, hidden-boundary retrieval summary, and corruption control without importing candidate code. `test_t1.py` is construction only; the frozen candidate CLI and separate raw-only audit CLI are each invoked once after a clean preflight. No retries or source repairs after formal execution.

Construction chronology: the first WSLc test command stopped before tests because the pinned base image has no `pytest`; no network or package install was used. The harness was converted during construction to standard-library `unittest`. Final host construction: 5/5; final pinned-image WSLc construction: 5/5. The initial setup failure is retained in `CONSTRUCTION_RESULT.md`.

## Allocation and preregistration

See [`PROTOCOL.md`](PROTOCOL.md) and its source/data identities in [`FREEZE.json`](FREEZE.json).

## Result

Allocation-01 completed: candidate exit 0 and separate raw-only auditor exit 0; retries 0. Raw result and audit are retained unchanged under `results/allocation-01/`. The auditor verifies the output (`audit_status=PASS`) but applies the frozen scientific gate as `FAIL_METHOD`: matched MRR improves over the unstratified baseline by 0.0729, below the preregistered 0.10 threshold. See [`REPORT.md`](REPORT.md) and [`RUN_RECEIPTS.json`](RUN_RECEIPTS.json). This is a finite synthetic method result only; empirical T0/T2 remain `HOLD_NO_COMPARABLE_SPECTRUM`.
