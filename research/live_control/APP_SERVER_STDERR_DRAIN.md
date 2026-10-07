# App-server stderr progress and bounded diagnostics

The journaled v2 client drains stderr on a separate thread. Its default Popen
stream is read as bytes, so invalid diagnostic encodings cannot stop draining.
The drain does not write the journal or acquire the protocol condition/write
locks. JSONL stdout remains the response/notification protocol; stderr never
creates a response, completion, usage, authority or task-effect receipt.

`stderr_snapshot()` returns a dictionary with an immutable raw `tail` of at
most 65536 bytes, `bytes_received`, `complete`, and `error`. It keeps only the
latest bytes while continuing to consume the stream. A text-only injected
process stream is encoded as UTF-8 for compatibility; its count describes that
adapter representation. Consumers must treat diagnostics as potentially
sensitive untrusted output. The raw tail can begin in the middle of an encoded
character; decode with an explicit error policy if presenting it to a user.

`complete` means stderr EOF was observed. A read exception is retained as a
bounded error description and leaves `complete` false; it is not EOF or a
verified complete diagnostic capture. Diagnostic capture is best effort and
not durable storage. A stream read failure can still prevent further stderr
progress. The client does not retry requests or interpret diagnostic text.

After terminating/reaping the owned peer, `close(timeout=...)` checks stdout
reader retirement, then stderr reader retirement, then the existing journal
lock/close boundary. An unfinished stderr reader raises TimeoutError and keeps
the journal open for later retirement. Timeout applies to individual waits,
not a single total wall-clock deadline; None retains the existing unlimited
wait behavior. An inherited diagnostic writer can therefore prevent successful
retirement until its owner releases the pipe. No hard OS release guarantee is
claimed. Pipe-handle closure remains the existing caller responsibility.

The new ordinary tests exercise a real owned stderr pipe with 1 MiB output,
invalid UTF-8, bounded exact tail retention, independence from a held journal
lock, read-error versus EOF distinction, and journal preservation while a
diagnostic writer remains live. Existing stdout EOF, late-frame retirement and
contended journal-close tests are retained. The pure journal-close fixture now
supplies both already-retired readers, matching the initialized client's state.

This repairs the transport prerequisite identified under Issue #57. It is not
evidence of actual provider failure frequency, model/GUI task success, physical
input release, useful feedback onset or a speed/token benefit. Prospective
review and then-current source/application gates precede any main adoption.
