# Bound command-pipe wait and retain partial-write uncertainty

`bounded_pipe_writer.py` is an unintegrated Linux candidate for an exclusively
owned, unbuffered pipe fd. It switches the fd to nonblocking, bounds UTF-8 record
size, and uses a monotonic deadline plus select instead of indefinitely blocking
write/flush. The caller must serialize writes. Any attempted-write exception
permanently poisons this writer: later commands cannot append bytes to a partial
JSON record. It neither retries the partial record nor claims runtime acceptance.

Real os.pipe controls with 4096-byte capacity:

| Case | Bytes written / requested | Outcome | Write duration |
|---|---:|---|---:|
| Complete Unicode record | 56 / 56 | pipe_written | 0.016 ms |
| Full pipe, reader not draining | 0 / 4234 | uncertain, poisoned | 100.291 ms |
| Partial record, reader not draining | 4096 / 4234 | uncertain, poisoned | 100.255 ms |
| Closed reader | 0 / 4234 | uncertain, poisoned | 0.017 ms |

CommandOnce wrappers do not repeat the write for the same request ID. A new
cancel request after poison also fails without a new write. This prevents corrupt
record concatenation but does not deliver cancellation; ordinary input lease
expiry remains a separate runtime property, not tested by these pipe controls.
The inherited CommandOnce success label stdin_flushed here means all bytes passed
to the unbuffered pipe, not that a consumer read or accepted the command.

Initial probe v1 derived a payload from a larger default pipe capacity, exceeding
the configured record limit. Pre-write validation correctly rejected it; the
probe incorrectly expected a write record and failed. That source and failure
description are retained in results/bounded-pipe-writer-01. Probe v2 fixes pipe
capacity before deriving its payload, then exercises all four intended conditions.
Successful evidence and source hashes are in results/bounded-pipe-writer-02.

This is kernel-pipe testing, not application self-use or a real-time guarantee.
Deadlines can overshoot under scheduling. The helper does not close or recover
the pipe, drain partial input, terminate the child, or clean up application state.
Its diagnostic list is unbounded. It is incompatible with concurrent buffered
TextIO writes on the same fd. Pre-validation failures are distinct from a partial
write internally, although CommandOnce still conservatively reports uncertainty.

Next integrate only with an explicitly unbuffered exclusive subprocess stdin and
test blocked-write shutdown, lease expiry and reconnect behavior. Do not append
finish/cancel to a poisoned stream or replace it with a fresh stream while an
old consumer may still act. Reserved cancel slots alone cannot fix a broken
shared command channel. No default promotion, human-speed claim or freeze credit.
