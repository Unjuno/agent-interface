# Issue #6532 — allocation timing receipt T0

This package is an additive, finite protocol experiment derived from #6274's unresolved chronology HOLD. It tests whether a timestamped record can be classified against a prospective `[start,end)` allocation window. It does not recover #6274's historical execution timestamps, prove any clock truthful, or validate its preference-choice result. Allocation-01 terminated as `STOP_CANDIDATE_INVOKED_OUTSIDE_FROZEN_CONTAINER_PROTOCOL`; see [REPORT.md](REPORT.md), [STOP.json](STOP.json), and preserved diagnostic output.

## H / T / D / C / U

- **H:** A finite receipt classifier distinguishes valid in-window execution from pre-window, post-window, contradictory report time, missing offset, reversed interval, unmapped clock, hash mismatch and exact boundaries; all uncertainty remains HOLD/STOP.
- **T:** Ten authored cases in `fixture.json`; candidate emits classifications and receipt fields, independent auditor reconstructs every field directly from raw fixture and rejects four output mutations. Formal route, when assigned: separate cached digest-pinned OrbStack containers, network disabled, one CPU, source read-only and result directory writable; candidate once, then independent auditor once only on candidate exit 0; retries 0.
- **D:** `PASS_METHOD_SCOPED` only when every row independently matches, every fully contained valid interval (including exact start) is eligible for the timing gate only, every invalid/ambiguous row is not eligible, four corruptions are rejected, and formal cleanup/integrity receipts pass. Any uncertainty falsely marked eligible is FAIL. Failed resource gate before candidate is STOP, invocations 0/0.
- **C:** Authored timestamps/clock IDs and booleans are trusted only as finite test inputs; their correspondence to real event time is not established.
- **U:** No truth about host/container clock accuracy, historical #6274 execution, external signer authenticity, GUI/model/task effect, or production allocation governance.

## Current formal status

The formal freeze/OrbStack candidate/auditor did **not** run because the only OrbStack daemon was occupied by another active worker's container and no exclusive CPU slot had been assigned (#5085 comment #5945709086). A mistaken host `--help` invocation nevertheless executed the candidate once; allocation-01 is stopped and must not be retried. Do not report construction tests or this host diagnostic as a formal experiment. Any continuation requires a fresh, distinct allocation identity after explicit release/assignment and a new prospective source/path/hash freeze.

## Local construction command

`python3 -B -m unittest -v research/analysis/timing_receipt_6532_t0_20261002/test_timing_receipt.py`
