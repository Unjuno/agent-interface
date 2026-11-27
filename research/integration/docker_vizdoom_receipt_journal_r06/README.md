# R06 hash-linked receipt-journal prototype

R06 implemented and tested an experimental single-writer JSONL receipt store
with per-record sequence, `effect_ref`-compatible name, payload digest,
previous-record digest and record digest. A scan rejects the entire journal on
missing newline, malformed JSON, sequence gap, duplicate reference, payload
tampering or hash-chain mismatch. Reopening builds an in-memory lookup index.
Append/flush failure freezes the live writer. The prototype is not connected to
the guarded X11 runtime.

Nine unit tests passed inside the pinned Docker image in normal Python and the
same nine under `python -O`. The tests cover exact payload lookup and order,
duplicate names, canonical JSON limits, payload tampering, sequence/hash-chain
checks, torn-tail rejection, external mutation and append-open failure.

Ten matched storage repetitions used the same 19 compiled receipts from R04
pair 19. All values resolved after reopen and compared exactly to the inputs.

| Method | Median append | Median verified readback | Median combined | Bytes |
|---|---:|---:|---:|---:|
| Pretty JSON, 19 files | 31.260 ms | 25.552 ms | 57.086 ms | 15,885 |
| Hash-linked JSONL prototype | 77.747 ms | 5.313 ms | 83.473 ms | 19,228 |

Combined append and readback was 46.2% slower for the prototype. It opens,
flushes, closes and size-checks on every append, so this result rejects the
naive per-event reopen design. The faster readback is a useful tradeoff, but
does not compensate for slower writes in this sample.

The journal is single-writer and flushes Python buffers without `fsync`. It
does not establish machine-crash durability, concurrent writer handling,
existing artifact-reader compatibility or live uncertain-delivery behavior.
The next prototype should hold one locked append stream for the session, flush
each event, fail closed on short writes or torn tails, and remeasure the same
receipts before any runtime integration.

The runner, prototype, test logs, 20 raw output directories, exact input
payloads, conditions and 213-file SHA-256 manifest are preserved in the
task-local packet `private-packets/docker_vizdoom_receipt_journal_currentmain_20261028_r06/`.
