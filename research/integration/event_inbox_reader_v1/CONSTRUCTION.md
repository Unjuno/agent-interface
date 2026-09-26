# Construction and retained-record transfer

Candidate source: `377690618` (reader, tests and initial README).
Local Docker image:
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
One construction container, network disabled, source/root read-only, 256 MiB
memory limit, 16 MiB writable /tmp. Exit 0. No GUI or native input.

Five test methods passed, including the real `DeliveryLedger.prepare` producer,
paginated/repeated reads, incomplete newline, changed prefix, wrong stream/cursor,
duplicate/gapped identities, malformed/ambiguous JSON and bounds.

The retained `journal-self-use-01/delivered.jsonl` Git bytes were read with
max_records=4. Four calls returned [4,4,4,3] records, matching all 15 original
payloads and their order exactly. A final read at the returned cursor was empty.
The source bytes remained unchanged; their SHA-256 is
`a5850cdd42eb8e298c35068f1933f7eef4ba0f23c14e7ac49593027172626df6`.
All responses remained authority=none and acknowledged=false.

Local command, source-file hashes, complete logs, transfer script and result are
retained at `results-local/passive-reader-construction-01/`. The original fixture
and old scientific allocations were not modified or rerun. This is a construction
check and historical record transfer, not a fresh interactive producer, model
delivery, persistent ACK, queue adoption, or measured performance improvement.

## Active producer component check

`python -m research.integration.event_inbox_reader_v1.active_check check NEW_DIR`
starts a separate producer using `DeliveryLedger.prepare` and five separate
reader processes. Each subprocess wait has a five-second bound; unfinished
children are killed and reaped. NEW_DIR must not exist.

The producer flushes one complete record and a second valid JSON object without
its final newline. The first reader returns only record 1. Two new readers load
the saved cursor and both leave the incomplete tail untouched. A test barrier
(not an ACK) permits the writer to append the newline and record 3. A new reader
returns records 2 and 3, exactly matching the producer payloads and order. The
last reader loads the advanced cursor and returns no records. All responses
remain authority=none, acknowledged=false, input_dispatched=false.

Windows run `passive-active-windows-02` and Docker container
`ai-passive-active-02` passed; Docker exited 0 using the same pinned image above,
network disabled, read-only root/source, 256 MiB memory and writable /tmp/output.
The stream SHA-256 in both runs was
`c307b0bcf8e438b647b1406d8a1f92ae556718facbca3762b45bc64e4805af5e`.
Detailed outputs are retained under `results-local/passive-active-{windows,docker}-02/`.
The initial Windows check failed because its test barrier compared LF literally
with Windows CRLF. Only barrier comparison was normalized; JSONL framing remains
strict. The initial Docker check passed. These are component checks, not a full
interactive_v17 run, GUI/model delivery, producer-restart recovery, durability,
concurrent rewriting or performance evidence.

The subsequent explicit host command check (`ai-passive-host-01`, exit 0)
replaces the test-only reader subprocess with the documented module CLI. It
passes the same five-process scenario and stream hash. Container
`ai-passive-host-tests-01` passed all six unit/CLI test methods, including
unchanged input files, repeated reads, persisted cursor reuse, null/malformed/
oversized cursor rejection, structured stdout and exit codes. A primary agent
invocation (`ai-passive-host-selfuse-01`) read the first two generated records
through that command and received `tail_state=limit` and `next_sequence=3`.
This is direct command use on component-generated records, not live GUI feedback.
All three containers use the pinned image and offline read-only source settings
above. This candidate still has no automatic host wakeup or production emitter.

Disposition: experimental candidate for review. Before runtime promotion,
decide the host API and lifecycle for explicit read cursors and owner-assigned
stream epochs. ACK/compaction and
multi-producer scheduling require separate contracts; they are not implicit in
this reader.
