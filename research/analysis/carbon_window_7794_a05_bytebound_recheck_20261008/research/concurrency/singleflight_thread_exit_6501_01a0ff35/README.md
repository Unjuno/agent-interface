# Last-waiter detach does not certify executor callable completion

Retained new ordinary #6501 construction, worker
`01a0ff35-0b9f-7d13-bcfa-22d064ff4fec`, FINAL-v5. Native Windows
`Windows-10-10.0.26300-SP0`, CPython 3.11.9, standard library only.
This research package changes no runtime or workflow. It does not import or rerun
T0/T0b, #6890's async-coroutine allocation, or the separate socket-scope study.

An asyncio wrapper can be terminal/cancelled while its already-entered executor
callable remains active. The local registry therefore needs the underlying
`concurrent.futures.Future`'s completion as its handback boundary. Python's
[Future cancellation/completion contract](https://docs.python.org/3.11/library/concurrent.futures.html#concurrent.futures.Future.cancel)
supports this distinction; the observed event counts below are this construction's
result, not documentation performance claims.

Source/oracle/plan freeze commit `9de26a4edfc8173ed31cc44f250b5ca59ec1d3de`
precedes the eight-row matrix. The runner checks all nine [frozen inputs](FREEZE.json).
New construction ID: `6501-THREAD-EXIT-NATIVE-20261003-01a0ff35-0b9f-A01`.
Actual matrix=1, independent raw-only auditor=1, retries=0. Both exit 0.

| Actual schedule | Wrapper cancellation retirement | Underlying Future retirement |
|---|---|---|
| Two stable waiters | One callable; two deliveries | One callable; two deliveries |
| One waiter cancels, one rejoins | One callable; two unaffected deliveries | Same |
| Last waiters cancel, rejoin before callable exit | Two callables overlap; rejoin delivers | One callable; rejoin YIELD until exit |
| Last waiters cancel, rejoin after callable exit | Fresh second callable; one delivery | Same |

All four last-detach checkpoints observe wrapper `done=True`, `cancelled=True`,
underlying Future `done=False`, `running=True`, and one active callable. The
candidate retains a CLOSING entry there; the comparator drops it. The early
rejoin is the sole intervention that exposes overlap: measured peak is two
versus one. These are four authored schedules, not prevalence/rate samples.

The original [v1 auditor](audit.py) covers strict event schema/types, contiguous
order, selected identities, balance and completion/count checks. All eight rows
match the prospective [decision table](PLAN.md); its eight predeclared controls
reject. Independent reviews then found five accepted causal/caller-role
contradictions. V1 is preserved as historical evidence and has incomplete
automated causal coverage. [Standalone v2](audit_v2.py) repairs the prior completed
wrapper, preceding unserved request and named caller-role joins, plus recorded
platform/UTC bounds. [Audit correction](AUDIT-v2.md) preserves the first RED and
all original bytes and distinguishes raw-only repair from experimental replay.
The original observed lifetime contrast remains unchanged. Raw SHA-256:
`179bf58c8cb3f42f439cd376c9a56dc18e413c60e96953055770a403f4ffe0e1`.
See [raw](evidence/raw.json), [audit](evidence/audit.json), and actual
[matrix](evidence/matrix.receipt.json)/[audit](evidence/audit.receipt.json) UTC/exit receipts.

Each row ends with zero active callables, terminal wrappers/Futures, empty
registry and joined executor. Eleven callables and 22 caller outcomes are
retained across the two policies. No input, network/socket, native backend,
container/WSLc, model, GPU, shared resource or additional agent was used.

Construction regression: retained RED has one assertion failure (two source
calls instead of one); after the conditional retirement repair, 3/3 pass.
The earlier [scaffold timeout](INITIAL_SETUP.md) is disclosed separately: it is
not the matrix outcome, and its unrecorded exact command endpoints/byte streams
are not invented. Later commands preserve original private byte streams and
public path-redacted derivatives with both SHA-256 identities. Public log bytes
retain CRLF; log-only attributes exclude irrelevant whitespace diagnostics.

From this package directory, read-only reproduction of the retained audit can use
an unused output path:

```text
python -B audit_v2.py evidence/raw.json NEW_AUDIT.json
python -B -m unittest -v test_audit_v2
```

Do not replay this frozen eight-row run as a new allocation. Future changed
questions need new identities, source/condition freeze and explicit differences.

`PASS_THREAD_LIFETIME_SCOPED` supports retaining a closing singleflight entry until
its owned callable actually finishes. This mechanism does not terminate arbitrary
blocked I/O or promise prompt recovery: a never-finishing callable must remain
pending and cause YIELD/escalation. Event-loop registry operations are sequential;
no concurrent registry, arbitrary scheduling, clock/generation trust, GUI/effect,
authority, throughput/latency/token advantage or product claim is established.
Physical thread termination is asserted only by the final executor shutdown,
separately from callable exit and Future completion. Source is isolated engineering
evidence, awaiting nonauthor review and any future runtime adoption decision.
