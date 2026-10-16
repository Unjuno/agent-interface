# Client-local endpoint instrumentation

prepared_exchange_v6.py retains the v5 request, admission, outcome and optional
drain behavior and adds phase timestamps. These are performance-counter wall
timestamps in the caller's described clock domain, not CPU attribution.

The marks cover main entry (after Python startup/imports), argument parsing,
source loading, program preparation, request persistence, clock description,
socket connection, sendall return, complete response-line receipt, JSON decode,
result/image processing, optional drain completion, report file write, stdout
serialization and stdout flush return. Phase differences include scheduling and
all work between adjacent marks. For example, program preparation includes reading
the steps file; result/image processing includes persisting the received reply.
File write completion is not an fsync durability guarantee. sendall return does
not establish runtime admission or remote consumption.

The final client-endpoints.json sidecar records the later stdout timestamps.
They cannot be included in a response serialized before they occurred. report.json
and stdout therefore contain only the marks available when each was serialized.
Consumers must not assume those three artifacts have identical endpoint coverage.
The sidecar write itself is outside the measured stdout interval. A crash or blocked
stdout can prevent the sidecar from being produced; there is no new hard deadline.

Model observation receipt, generation start, generation end and result receipt
are explicitly null. Local pipe flush return is not a model receipt timestamp.
The cached domain assumes the process does not change its time namespace.
Endpoint uncertainty and instrumentation overhead remain unmeasured.

## Integrated evidence

probe_client_endpoints_live.py runs the actual Linux/X11 Calc fixture with scripted
input and a gated evaluator. Both caller programs expose all 15 marks in order,
all model endpoints remain null, and the runtime/caller clock domains agree.
The full 12-frame reconstruction, saved workbook values/hash, two admitted
programs, verified release, retained event prefix and request lineage pass.
The caller returns early while evaluation is gated, then receives successful
independent evaluation after the gate is released. No model self-use is claimed.

| Adjacent-mark interval | Entry | Confirmation |
|---|---:|---:|
| Source loaded to program prepared | 8.200 ms | 57.686 ms |
| Program prepared to request persisted | 8.124 ms | 37.991 ms |
| sendall return to complete response line | 787.822 ms | 167.988 ms |
| Complete line to JSON decoded | 0.435 ms | 0.081 ms |
| JSON decoded to result/image processed | 25.091 ms | 23.316 ms |
| Result/image processed to optional drain finished | 0.004 ms | 8.313 ms |

These are two calls in one run on WSL with the repository on /mnt/c. The unequal
preparation times cannot be attributed to file I/O, scheduling, or input size
without a controlled comparison. The marks expose previously omitted preparation
and persistence costs; they do not establish a performance regression or gain.
The response wait includes runtime work, transport and scheduling, not just network.

Keep v6 optional. Next use the endpoint breakdown in actual self-use and compare
equivalent preparation/persistence on controlled storage, without weakening exact
request persistence or evidence checks. This does not complete Issue #46 or its
Calc/OpenTTD comparison. Evidence and source hashes: results/client-endpoints-live-01.
