# Actual self-use through a private observation socket

`event_socket.py` wraps frozen interactive_v23. The child retains inherited stdin
for ordinary commands; stdout is copied into EventCursor. A read-only Unix socket
in a mkdtemp 0700 directory accepts only after/events/timeout fields. It exposes no
submit endpoint, TCP listener or authority renewal. The CLI read process returns
one JSON batch then exits; the original process remains active for input.

The assistant inspected initial and modal images and performed the known Calc
532/590 save using two programs, two clocks and six socket read calls. The effect
batch ended at delivery:24; a separate call retrieved final evaluation delivery:25.
Both were actual model-facing tool calls. The final event had already been emitted
before the effect read returned, so this does not demonstrate pre-final model
wakeup. Saved values, artifact digest, receipts, twelve exact AIT/PNG frames and
the complete concatenated 25-record read prefix are audited.

| Measurement | Value |
|---|---:|
| First capture to effect emit | 75.394 s |
| First capture to effect socket return | 77.053 s |
| Modal terminal to confirmation admission | 27.360 s |
| Final terminal to early effect emit | 19.595 ms |
| Early emit to socket return | 1658.709 ms |
| Local enter/save / confirmation programs | 750.839 / 138.211 ms |

This is a functional separation result, not a speed improvement. The prior direct
stdin self-use took 38.723 s to effect emit; the present 75.394 s includes extra
read calls, implementation inspection and model/tool scheduling. Sequential known
tasks do not isolate transport causality. No model-receipt timestamps or actual
token counts are available. Extra reads make this route unsuitable for promotion
on latency evidence so far.

Limitations: single sequential socket server; a slow read can delay another read
up to the bounded timeout. Record retention is count-bounded, not byte-bounded.
No session incarnation in cursors; no reconnect across restart. Normal child exit
cleans up the socket and drains the stdout thread; interrupted parent/child fault
cleanup and disconnect/slow-reader integration still require tests. Read replies
can be replayed but are not acknowledgements or current input authority. This is
trusted local research transport, not a supported public service.

Next combine command submission and one event-boundary wait in a single caller
operation, preserving ordinary runtime admission and explicit command identity;
avoid simply adding more polling. Evaluate matched tasks and failure handling
before claiming latency improvement. No default promotion or freeze credit.

Evidence: `results/event-socket-self-use-01`, including six read responses and
transport source hashes. `audit_event_socket_self_use.py` writes
`results/event-socket-self-use-audit.json`.
