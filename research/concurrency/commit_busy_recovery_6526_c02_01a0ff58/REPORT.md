# Known COMMIT-BUSY recovery: native compatibility C02

One directed six-condition ordinary native construction completed on Windows CPython 3.11.9 / SQLite 3.45.1. This decides the simplest recovery after a **known, returned reader-caused COMMIT SQLITE_BUSY while the same transaction remains active**. It does not resolve a lost commit response or grant task/input authority.

| Journal | Policy | First COMMIT | Active after first | UPDATE count | Fresh revision |
|---|---|---|---|---|---|
| DELETE | Release owned reader first | success | false | 1 | 1 |
| DELETE | After BUSY, release reader and retry COMMIT only | SQLITE_BUSY | true | 1 | 1 |
| DELETE | After BUSY, release reader and repeat UPDATE before COMMIT | SQLITE_BUSY | true | 2 | 2 |
| WAL | All three policies | success | false | 1 each | 1 each |

Adopt the existing COMMIT-only operation for this narrow state. The deliberately weak UPDATE-again comparator produces a duplicate revision. WAL controls never enter recovery because their first COMMIT succeeds. Ending an observer's transaction requires ownership; an expired/revoked action must not acquire new authority from this result.

SQLite's transaction manual section 2.3 explicitly describes this reader-caused BUSY case: the transaction remains active and COMMIT can be retried after the reader clears. Other error classes may end a transaction. Source: https://www.sqlite.org/lang_transaction.html (read 2026-10-03). This is API compatibility evidence, not a novel algorithm.

H/T/D/C/U, environment/executable/source hashes and six fixed cells are in freeze.json, created before the sole execution. Producer ran 12:11:28.208989-12:11:28.614776 UTC, exit0; first raw and six closed DBs retained. Separate endpoint subprocesses read revision/integrity after writer/reader close, each exit0, zero changes, integrity ok. Another implementation reconstructed raw SQL/update/commit counts and read fresh exact DB copies, then refused four effective copied-data corruptions (boolean revision, missing BUSY, hidden duplicate, erased COMMIT trace). Audit ran 12:11:41.100118-12:11:41.185996 UTC, exit0. Same-author separate reader/process, not independent human review. Timestamps are execution receipts, not latency measurements.

Original C01/#6925 sixteen-case producer, first auditor FAIL, native bundles and GUI A01/A02/A03 were neither reopened nor replayed. C02 uses six new private DBs, a new output namespace, one finite deck, no repeat. No shared GUI/GPU/model/container resource, runtime change or main request.

Scope: single-thread separate native connections; known standard SQLite locking; private integer-row fixture. Excludes lost response, crash/power loss, arbitrary app effects, deadlines/cancellation races, model/token benefit, population frequency, GUI observation-intervention and broad #6526 H_PASS. No callback/controller implementation is promoted. Native API recovery alone does not establish an external task's success.

Files ending .py.txt are inert source preservation, absent runtime imports/test discovery/workflows. To reproduce a fresh ordinary demonstration in a new directory, restore them as assay.py/audit.py, create a new freeze with actual environment/source identities, and retain the new run separately; never overwrite first evidence. audit.py reads only exact fresh DB copies. Six .db.b64 capsules restore native bytes losslessly; decoded hashes are independently bound by rows.jsonl and PUBLIC_PROJECTIONS.json. Original private command records remain controlled locally; public projections retain exact command times/status/stream hashes while replacing private argv paths. No end-time receipt is invented.

Parent #6526; prospective claim https://github.com/Unjuno/agent-interface/issues/6526#issuecomment-5969017529. Content base a06d7f77367190b90350c34624647e8bc0d4b0fd. Bounded all-state prior-work intake found adjacent #4063/#4303/#4397, no retrieved identical deck; unpublished work unknown. #6925 remains unchanged and awaiting its independent content review. Main delivery remains separately gated by FINAL-v5 exact-content agreement and fresh actual-tree qualification.
