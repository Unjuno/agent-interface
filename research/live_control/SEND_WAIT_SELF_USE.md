# Combined command send and event wait in actual assistant use

Private `event_socket_v2.py` accepts an optional command and request ID alongside
the existing cursor read. It validates read parameters before forwarding the
unchanged command to interactive_v23 stdin, then returns the requested event
prefix. Runtime sequence, lease, focus and step admission remain unchanged. The
socket now permits commands and is restricted by its Linux 0700 parent directory;
it is not the previous read-only endpoint. No TCP service is added.

`command_once.py` serializes writes and remembers canonical command payloads by
request ID. Repeating an identical request performs no second write; conflicting
payloads are rejected. A write/flush exception remains write_uncertain and is not
retried. Registry capacity rejects new requests instead of evicting IDs. This is
at-most-one write attempt within a single live process, not exactly-once input or
application effect. No persistent retry identity survives server restart.

The assistant viewed initial and format-dialog images, entered 532/590 and
confirmed Excel through two shared programs. It then repeated the same confirmation
request ID while reading final evaluation. The reply says replayed=true and the
runtime command log contains exactly one confirm_excel command, one admission
and one successful save. Five caller operations cover initial clock/observation,
enter/save, second clock, confirmation/effect, and final result; cleanup is separate.

| Metric | Separate send/read prior run | Combined send/wait run |
|---|---:|---:|
| First capture to effect socket return | 77.053 s | 57.422 s |
| Modal terminal to confirmation admission | 27.360 s | 23.168 s |
| Effect emit to socket return | 1658.709 ms | 5.491 ms |
| Caller command/read operations through final result | 10 (4 writes + 6 reads) | 5 |

The new early socket return precedes final evaluation emission in the local clock.
This does not prove the model resumed before final scoring: process serialization,
WSL/exec return and model scheduling are outside that timestamp. This actual use
is one familiar sequential run per route, not a randomized causal comparison.
It remains slower in total than the earlier direct-stdin run; human-like tempo
and model token savings remain unproven. Extra token fields are not token savings.

Verification: saved workbook [532,590] and effect hash, twelve exact AIT/PNG frames,
unchanged final score, flush receipts and complete 25-record response prefix.
Unit controls test duplicate, conflicting payload, registry full, uncertain write,
and eight concurrent same-ID calls (one write attempt). They do not simulate a
live socket disconnect or server crash. Results are in
`results/send-wait-self-use-01`, `results/send-wait-self-use-audit.json`, and
`results/command-once-01.json`.

Limitations: single sequential socket server, synchronous stdin writes, in-memory
deduplication, record-count rather than byte limits, no restart-safe cursors or
durable receipts. A blocking command write or read can delay other requests,
including cancel. Existing runtime leases still expire independently; this does
not establish fast cancel responsiveness through the bridge. Process interruption
cleanup and live disconnect/retry cases remain unverified. No default promotion
or freeze credit. Next test delayed/disconnected reads and cancel head-of-line
blocking before broadening this bridge or claiming performance improvement.
