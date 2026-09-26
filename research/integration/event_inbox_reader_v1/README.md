# Passive event-reader integration candidate

Issue #3876. This is an experimental, explicit read API for the existing
`interactive_v17` / `DeliveryLedger` prepared `delivered.jsonl` format. It is
not enabled in the production CLI, MCP server or portable distribution.

An explicit experimental command is available from the repository root:

```sh
python -m research.integration.event_inbox_reader_v1 --stream /owned/run/delivered.jsonl --stream-id owned-run-epoch-1
python -m research.integration.event_inbox_reader_v1 --stream /owned/run/delivered.jsonl --stream-id owned-run-epoch-1 --cursor /owned/cursor.json
```

The host saves the returned `next_cursor` object separately after handling the
response. This command does not write a cursor or modify the stream. An omitted
cursor starts at the beginning; it is not a recovery fallback. Use the same
owner-assigned stream identity only within that run. If stdout is lost, reading
again with the same cursor repeats records without repeating any actions.
The response is one JSON line. Exit 0 includes incomplete tails and page limits;
inspect `tail_state`. Exit 2 indicates a blocked record or read failure. A blocked
response can contain earlier valid records and a cursor before the bad record;
a read failure supplies no next cursor. Do not discard pending records or reset
the cursor to hide either condition. Cursor files are bounded to 4096 bytes.

`read_pending(path, stream_id=..., cursor=..., max_records=32, max_bytes=1048576)`
returns complete newline-terminated records, in original order, and a next read
cursor. The caller assigns a new stream identity for each owned run/epoch and
keeps the returned cursor. The cursor binds its byte offset and next sequence to
the SHA-256 of the entire consumed prefix; it is not authentication or authority.
Repeated reads with the same cursor deliberately return the same records.

The supported producer is one append-only writer with contiguous `delivery:N`
identities beginning at 1. Duplicates, gaps, invalid objects, duplicate JSON keys
and non-finite JSON constants block at the offending record. Earlier valid
records may be returned; the next cursor stops before the offending bytes.
Neither skipped records nor synthetic predecessors are created. A valid JSON
object without its terminal newline is still an incomplete tail. Appending that
newline allows the next explicit read to return it.

Every response states `authority=none`, `acknowledged=false` and
`input_dispatched=false`. Reading does not remove records, create an ACK,
resynchronize a producer, poll in the background or execute input. Existing
flush evidence and native submit/resume behavior are untouched.

The full bounded snapshot is read and its consumed prefix rehashed on each call.
The default file-size ceiling is 1 MiB, configurable up to 64 MiB; exceeding it
raises an explicit error, not partial success or log rotation. This construction
does not establish long-session efficiency. A caller must handle such a limit
without silently resetting its cursor or deleting history.

Assumptions/limits: trusted local append-only producer; no atomic snapshot against
concurrent rewriting, hostile-file authenticity, filesystem durability, recovery
of a producer's in-memory sequence allocator, persistent acknowledgement,
compaction, multi-producer arbitration or model receipt proof. A byte-identical
prefix does not identify a process incarnation; the owner must supply epoch
identity. No timing threshold, queue capacity or performance gain is inferred.

Construction checks use the actual `DeliveryLedger.prepare` implementation and
exercise pagination, repeat reads, partial tails, changed prefixes, mismatched
stream/cursor, duplicate/gap/malformed records and explicit bounds. A separate
read-only transfer check can consume the retained `journal-self-use-01`
prepared payloads. Neither is a rerun of #717/#742/#916/#926 allocations.
