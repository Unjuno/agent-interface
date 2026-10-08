# Distinguish socket command rejection, partial write and unusable channel

Private socket v6 uses typed writer failures and CommandOnce v2 receipts:

* rejected_before_write: a bounded record validation fails before any os.write;
  this does not poison the writer.
* write_uncertain with sent/total and channel_poisoned: an attempted write fails;
  the bridge closes stdin and does not wait for the requested application event.
* channel_unusable: a later request reaches an already-poisoned writer and sends
  zero new bytes. The old request's replay retains its original partial receipt.

Generic unexpected callback errors remain conservatively write_uncertain without
invented byte counts. These receipts describe transport state, not runtime admission,
semantic completion or a successful cancellation. Registry identity is process-local.

## End-to-end live fault evidence

`socket_pipe_fault_entry.py` substitutes the existing paused-stdin test runtime
behind actual event_socket_v6 and sets its pipe capacity to 4096 bytes. Requests
travel through the Unix socket, handler, registry, writer and real interactive_v23.
No production runtime source is modified.

The probe first sends a UTF-8 request below the socket input limit whose canonical
escaped command exceeds the writer limit. It receives rejected_before_write with
zero bytes, then successfully sends a clock. It starts a held Right key with an
800 ms lease while the test runtime pauses its stdin iteration for two seconds.
An 8028-byte command then writes 4096 bytes and returns write_uncertain in
101.179 ms, including the socket round trip. Same-ID retry returns the retained
receipt without another write. A new cancel request returns channel_unusable and
does not appear in the runtime command log. A read-only request still retrieves
the eventual expired terminal with verified release; runtime exits normally.

Only the original successful clock executes. Source hashes, exact observation
frames and verified owner close are checked by audit_socket_pipe_fault.py.
Evidence: results/socket-pipe-fault-01 and results/socket-pipe-fault-audit.json.
The request log summarizes padding length instead of copying repeated payloads;
the probe source defines their exact construction.

This is a single scripted known failure, not a latency bound or assistant speed
comparison. The reader pause is test instrumentation; a consumer that never resumes
can still prevent shutdown. Cancel is not rescued after a partial command; expiry
remains the fallback. Lock-wait time, restart identity and unavailable-child handling
remain open. Successful pre-write rejection is not permission to alter/retry a
side-effecting request automatically. No default promotion or freeze credit.

Next review transport outcome names and correlate requested boundaries with action
IDs before returning these outcomes to general live planners. This closes the prior
end-to-end fault-evidence gap but does not establish a production shutdown contract.
