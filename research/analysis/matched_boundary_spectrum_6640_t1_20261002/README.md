# Matched-run boundary spectra — Issue #6640 T1

Frozen hypotheses, experiment, decision rule, scope, and allocation are in [`PROTOCOL.md`](PROTOCOL.md).

## Construction / formal separation

`make_fixture.py` creates the exact fixture and hidden oracle. `candidate.py` never reads `oracle.json`. `auditor.py` independently reconstructs every ranking, row/seed denominator, hidden-boundary retrieval summary, and corruption control without importing candidate code. `test_t1.py` is construction only; the frozen candidate CLI and separate raw-only audit CLI are each invoked once after a clean preflight. No retries or source repairs after formal execution.

Construction chronology: the first WSLc test command stopped before tests because the pinned base image has no `pytest`; no network or package install was used. The harness was converted during construction to standard-library `unittest`. Final host construction: 5/5; final pinned-image WSLc construction: 5/5. The initial setup failure is retained in `CONSTRUCTION_RESULT.md`.

## Allocation and preregistration

See [`PROTOCOL.md`](PROTOCOL.md) and its source/data identities in [`FREEZE.json`](FREEZE.json).

## Frozen result

Pending the one-shot candidate and separate auditor. This section must preserve the first raw result, including FAIL/HOLD/STOP, without rerun or relabeling.
