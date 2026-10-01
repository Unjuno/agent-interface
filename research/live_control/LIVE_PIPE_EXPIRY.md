# Nonblocking stdin integration and expiry during partial writes

Candidate event_socket_v5 uses an unbuffered subprocess pipe exclusively through
BoundedPipeWriter. On a poisoned write it closes stdin, preventing later records
from joining a partial JSON line. A write_uncertain receipt returns immediately
as command_uncertain instead of waiting for an event that may never arrive.
Ordinary read-only requests still use the retained cursor while the server lives.

## Distinct verification scopes

1. A live socket-v5 xterm run repeats the long-read/cancel and disconnected-clock
   retry experiment. Cancel response is 52.898 ms, terminal is cancelled, owner
   release and close are verified, and the retried clock is not duplicated.
2. A separate direct-pipe harness runs the real interactive_v23 with a test-only
   stdin iterator pause before the third command. The already admitted Right-key
   hold has an 800 ms lease; stdin pauses for two seconds while executor and input
   owner continue. The harness writes an 8031-byte record through a 4096-byte pipe.

The fault writes 4096 bytes, then times out after 100.195 ms. Closing stdin leaves
an incomplete JSON record at EOF. While the stdin iterator is still paused, the
hold expires and verified release occurs 48.225 ms after the lease deadline.
When reading resumes, the partial record is rejected, no extra clock executes,
and the runtime exits with code zero and verified owner close. This establishes
expiry independence from this stdin-loop pause, not a general scheduling bound.

The direct-pipe fault is not end-to-end socket-v5 failure injection: it exercises
the same writer, EOF behavior and real runtime but does not prove the socket's
command_uncertain reply during the fault. Preserve this distinction. A consumer
that never resumes may remain alive after EOF closure; no bounded child-exit
guarantee or emergency process termination policy is implemented.

`audit_live_pipe_expiry.py` verifies listed source hashes, twelve exact AIT/PNG
observations, terminal statuses and owner close. Results are retained in
`results/socket-bounded-write-01`, `results/live-pipe-expiry-01`, and
`results/live-pipe-expiry-audit.json`. The fault source is stdin_pause_entry.py;
production interactive_v23 is unchanged.

## Remaining limits

CommandOnce serializes writer calls; the 100 ms budget covers one write attempt,
not time waiting for the registry lock. Its generic write_uncertain state also
covers pre-write validation errors; v5's 'channel unusable' recovery wording is
too broad for a validation rejection that did not poison the writer. Do not use
that wording as proof of EOF or input release. Next distinguish pre-write rejection,
partial transmission, poisoned channel and confirmed runtime termination in the
transport response, and test the socket failure path directly.

These scripted Linux cases do not establish assistant speed, server-crash recovery,
restart-safe identity or a reliable product shutdown contract. No default promotion
or freeze credit; retain the failure/expiry lineage for subsequent revisions.
