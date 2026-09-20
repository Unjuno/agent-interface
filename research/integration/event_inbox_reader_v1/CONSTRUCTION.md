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

Disposition: experimental candidate for review. Before runtime promotion,
exercise an actual active append-only producer and its owner-assigned stream
epoch, and decide the host API for explicit read cursors. ACK/compaction and
multi-producer scheduling require separate contracts; they are not implicit in
this reader.
