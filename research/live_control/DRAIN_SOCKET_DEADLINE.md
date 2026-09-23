# Bound optional final-drain I/O without losing early evidence

Zero server event wait does not bound a stalled socket response. The optional
final drain previously inherited a 35-second socket timeout, which could delay
returning already available early evidence. unix_json_deadline.py now applies
one absolute monotonic deadline across connect, send and all receive iterations.
Each operation gets only the remaining duration; a trickling peer cannot reset
the budget. It accepts one newline-delimited JSON response with an explicit
8 MiB default maximum and preserves the existing 16 KiB request line bound.

Candidate prepared_exchange_v4 uses this helper with a 250 ms deadline for the
optional drain only. The initial input send/wait is unchanged. drain_final retains
the early result and a separate error on timeout, truncation or malformed data;
no new input or status command is sent. Partial bytes are not promoted to evidence
or retained as a valid reply. An uncertain read can be inspected/repeated through
the existing cursor policy; this helper performs no retry.

Six cases use real private Unix sockets with a controlled peer and recorded
early/final payloads:

| Peer behavior | Time to return | Result |
|---|---:|---|
| Complete valid final reply | 0.481 ms | evaluated |
| No reply | 250.738 ms | retain early evidence + timeout |
| Bytes every 30 ms without a complete line | 250.847 ms | retain early evidence + timeout |
| Partial line then close | 0.596 ms | retain early evidence + EOF |
| Malformed JSON line | 0.577 ms | retain early evidence + parse error |
| Response over configured test byte limit | 0.372 ms | retain early evidence + limit error |

Every case sends exactly one read-only request with server timeout zero. All
fault cases keep task_success unset rather than reporting failure or success.
The size control uses a 64-byte test bound to exercise the same rejection path;
it is not an 8 MiB memory/load benchmark. These peers do not run a GUI runtime.

An additional full CLI/Calc evaluation-gate run verifies integration: twelve
exact frames, saved workbook/hash, both input releases, lineage and full prefix
pass. The CLI returns early before gate release, and its continuation receives
final success afterward. This is scripted evidence. It does not combine a live
GUI with a proxy-injected socket fault or measure actual assistant timing.

The absolute budget covers socket I/O, not JSON parsing, local file writes,
process scheduling or a hard real-time wall limit. A 250 ms optional wait is a
candidate tradeoff, not a universal optimum. The initial send and other clients
still use their existing timeouts. No human-speed, token-saving or default
promotion claim is made.

Evidence: results/drain-socket-faults-01 and results/live-drain-delay-02, with
their probe sources, raw records and source manifests. Next evaluate whether
the optional drain's added overhead is useful across non-Calc tasks, avoiding
applying an extra read where a final evaluation already ended the first call.
