# Concurrent identical durable receiver delivery — A2

Decision: **RETAIN_CONCURRENT_IDEMPOTENCY_SCOPED**.

A1 is retained separately as `INCOMPLETE_SUPERVISION_TIMEOUT`; no A1 case was rerun. A2 uses fresh d001-d030 identities and changes only outer supervision into six five-case invocations plus a mutation-driver no-op repair. `receiver.py`, `worker.py`, `run.py`, and the independent `audit.py` are byte-identical to the A1 measurement freeze; receiver.py remains the merged #337 predecessor blob.

All 30 A2 first cases completed. In every case two local subprocesses passed a common start barrier and both entered receiver calls before the first commit. SQLite `BEGIN IMMEDIATE` serialized the write transaction. Exactly one process committed the effect/terminal decision; the other returned that durable receipt through `outcome_first`. Both concurrent callers returned the same APPLIED receipt, the durable DB contained exactly one effect and one decision, and a later fresh-process replay returned the same historical receipt with zero new effect and no authority. Independent audit passes 30/30; seven guaranteed non-no-op corruption controls are rejected.

This is evidence for the existing transaction/idempotency shape at this local SQLite boundary. It is not a distributed exactly-once result. The start barrier establishes overlapping calls before first commit, not simultaneous CPU execution. `BEGIN IMMEDIATE`/SQLite writer serialization is part of the mechanism. No power-loss, network partition, retention expiry, multi-host, authentication, GUI effect, throughput or natural reliability-rate claim is made.

The next single-factor question is concurrent same-ID **different-content** delivery: preserve all mechanics and race two distinct fingerprints. The desired boundary is one durable request/effect outcome and one CONFLICT response, with no second effect or ambiguous durable decision.
