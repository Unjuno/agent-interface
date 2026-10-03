# Actual waiter deadline boundary — #6501 A01

One frozen ordinary native construction matrix and one separate raw-only audit
ran on Windows / CPython3.12.10, exits0/0, retries0. Thirty conditions produced
60 waiter outcomes. The result is `PASS_WAITER_DEADLINE_CONSTRUCTION_SCOPED`.
All eight copied-output corruptions were rejected; every owned task was terminal.

| Consumer policy | Conditions | Late descriptive admissions | Companion cancellations |
|---|---:|---:|---:|
| direct wait_for | 10 | 4 | 2 |
| shield only | 10 | 2 | 0 |
| shield + each waiter's delivery-time deadline check | 10 | 0 | 0 |

These are authored finite conditions, not independent samples or performance
estimates. Both fresh READY cases per policy admitted; UNKNOWN was never upgraded.
Each condition uses one actual shared asyncio Task and two same-scope waiters.
The companion intentionally has no deadline; the timed caller has its own deadline.
Producer behavior is cooperative cancellation or a planted coroutine that catches
CancelledError, sleeps100ms during authored cleanup and returns descriptive data.

Direct wait_for can return that value after its deadline, and cancelling the
cooperative shared producer also cancels the companion. Shield keeps the companion
alive, but a result obtained before the deadline can still be adopted after the
separate authored admission delay. Combining shield and a per-waiter final deadline
check refuses those values. This is a transfer/construction result, not a proposed
production broker, an actuation token, or a discovery that CPython violates its API.
The [official wait_for documentation](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait_for)
states cancellation completion may extend the total wait; its cancellation
behavior and shielding are separate from a caller's result-admission rule.

## First outcomes and freeze

The first three-method scaffold deliberately omitted the deadline predicate;
two methods failed. Its exact source/tests and log are retained. After the guard
was added, the5ms timer construction still failed: it observed a TimeoutError
before the perf-counter deadline although the producer returned READY. A diagnostic
showed perf-counter resolution100ns and monotonic/event-loop resolution15.625ms.
Those sources/logs/clock details remain separate construction evidence. No formal
matrix had yet been invoked.

Before collection, the plan changed the small interval to50ms (above two observed
loop resolutions), kept fresh/UNKNOWN at1s, and added the explicit100ms cancellation
cleanup and40ms post-deadline admission margin. Three construction methods then
passed. These parameters are authored controls, not measurements of backend I/O.
FREEZE.json pins candidate/audit/runner/fixtures/plan, interpreter and five actual
asyncio stdlib files. The original source-freeze commit is held privately because
its diagnostic logs contain private paths. Public source/input bytes match every
frozen hash; public logs are redacted derivatives, with original custody retained.
No private commit history is pushed.

The actual matrix records source hashes, actual UTC start/end and perf-counter
deadline/decision/event timestamps. All deadline comparisons use this one clock.
The event loop's timer is a scheduling mechanism; TimeoutError alone is not proof
that the perf-counter deadline elapsed. No early timeout appeared in the retained
50ms matrix, and all authored late returned values were verified late. Independent
oracle errors0; raw SHA256
`52501217edc60fbe8ba8e55872f567aa45d18a09f212a0406274aff197d80f12`.
Raw size52722 bytes. Actual command/exit receipts and first outputs are immutable.

## Scope and decision

H/T/D/C/U and the frozen decision rules are in PLAN.md. The raw-only auditor uses
literal condition rules and ordered events without candidate/runtime imports. It
checks all30 rows, both waiters, exact JSON scalar identity, source/runtime pins,
fresh/late timing, cancellation propagation and cleanup. Its separate implementation
is by the same author; it is not external non-author content review.

No previous #6501 T0/T0b/6890 candidate or formal allocation was rerun. Dynamic
joins and blocking executor exit remain owned by other workers and are outside
this study. No sockets, containers, backend, GUI, input, model, GPU or shared lane
was used. This does not establish production currentness, physical deadlines,
native release, naturally arriving workloads, runtime adoption, task effect,
latency benefit or general computer control. The fleet deadline/N remain unknown
and were not changed. Main integration requires FINAL-v5 fixed content review,
two eligible non-author approvals, exact current-base combination and conditional
application under actual GitHub requirements.

Use fresh output names for any permitted ordinary checks. Never replace raw.json
or consume this one-shot comparative construction again to obtain PASS:

```sh
python -m unittest discover -s research/concurrency/singleflight_waiter_deadline_6501_01a0ff2d -p test_construction.py -v
python research/concurrency/singleflight_waiter_deadline_6501_01a0ff2d/audit.py research/concurrency/singleflight_waiter_deadline_6501_01a0ff2d/raw.json /fresh/audit.json
```
