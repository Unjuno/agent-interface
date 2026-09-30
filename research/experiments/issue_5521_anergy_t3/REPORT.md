# T3 matched expiry-policy fork — host construction

## Result

PASS_HOST_CONSTRUCTION for the frozen 10-event schedule. Raw JSONL is retained
in raw-host.jsonl. clear-on-expiry and tombstone-on-expiry use identical event
inputs and evidence generations; only the tick-9 expired Q/A disposition
differs.
After main advanced, source/tests were refreshed and rerun at base
8be656666be2c9aea7196e33d327fd088cbba6fd; deterministic raw bytes were unchanged.

| Arm | Verifier checks | Admitted effects |
|---|---:|---:|
| Clear record at expiry | 6 | 4 |
| Retain EXPIRED tombstone | 5 | 3 |

At the expiry event, clear-on-expiry rechecks the same fingerprint at the same
generation and admits on SAFE; tombstone-on-expiry refuses without a check.
Both arms survive two worker-process exits/relaunches with matching serialized
state digests. They refuse the generation-1 contradictory case, and neither
emits a generation-1 effect. The independent auditor checks 29 raw records,
all six worker exits, restart state digest continuity, matched schedule,
policy-specific expiry behavior, and aggregate counts. Three unittest checks
pass, including disposition-swap and altered-expiry-generation mutations.

## Construction failures retained

The first auditor draft expected 35 records; observed runner output was 29
(one freeze, 14 rows per arm, and summaries included within those arm records),
so that audit invocation stopped on cardinality before evaluating semantics.
The first summary assertion also expected one fewer check per arm than the
registered event path actually generated. Both were harness expectation errors;
the output was not accepted until the corrected auditor and all three tests
passed. No source/result bytes were overwritten from T1.

## Scope

The runner launches fresh host subprocesses per segment; the parent carries
state as JSON stdin between exited workers. This verifies process-boundary
serialization, not OS/container failure recovery, disk durability, atomic file
replacement, or storage corruption. No Docker/OrbStack command ran: #5085
currently prioritizes the separate #5156 CPU lane and has no #5521 lease. The
T3 experiment remains incomplete until the matched arms run in an authorized,
network-disabled Linux container and a separate raw-only audit passes. This
does not establish fingerprint semantics, GUI safety, probe non-interference,
fairness, usefulness, or a preferred expiry policy for production.

## Reproduction

From repository root:

```sh
python3 research/experiments/issue_5521_anergy_t3/run.py > raw-host.jsonl
python3 research/experiments/issue_5521_anergy_t3/audit.py < raw-host.jsonl
python3 -m unittest discover -s research/experiments/issue_5521_anergy_t3 -p 'test_*.py' -v
```
