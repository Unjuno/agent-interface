# Host connection decision

Disposition: retain this implementation as a research integration candidate;
do not expose it in the production CLI/MCP or imply #3876 is complete.

Source review: `interactive_v17.main` reserves a fresh output directory with
`exist_ok=False`, creates one in-memory DeliveryLedger, and serializes its emit
path under one lock. It does not persist an epoch identifier. A directory name,
PID, file modification time, or reader-generated random ID is not a durable
producer identity. Public `runtime.cli_v1.attempt.invoke` instead persists a
request and one final report; it is not a source of this progress stream.

For the current explicit command, the owner must establish the mapping from
one producer lifetime to one stream ID before the first read and retain it
alongside its cursor. The reader cannot independently establish that mapping.
Do not generate a new ID on every read or continue an old cursor after a
producer restart. Prefix checking detects changed consumed bytes; it cannot
distinguish two lifetimes with identical bytes and the same supplied ID.

The candidate command deliberately returns a cursor without saving it. The host
must retain the response before advancing its cursor. A crash between response
handling and cursor persistence may repeat notifications. No exactly-once
handling is promised. A cursor is only read progress, never model consumption,
an ACK, completion of an action, or permission to replay input. Reading an empty
tail is not evidence that the producer has terminated. File-size overflow and
blocked records require an explicit host decision; resetting to offset zero or
silently skipping a record is not recovery.

Before production promotion, an existing production producer/host pair must
own and persist an epoch at run creation and define its terminal state. Its
host must explicitly route the ordered records to a supported presentation
without inferring schema compatibility merely because both use JSON. Add
coverage for normal termination, interrupted output, reader restart and a fresh
producer lifetime. These checks must inspect received response bytes and
original payloads. Do not add a synthetic background producer to satisfy this
gate. An ACK/retention/capacity contract remains separate work under #3876.

The current active check validates actual DeliveryLedger preparation and the
new read command across processes, but not interactive_v17, a production emitter,
automatic host wakeup, model receipt, decision fidelity or useful-feedback time.
Those missing endpoints prevent a production or performance claim. The
historical 15-record corpus remains immutable and does not substitute for them.
