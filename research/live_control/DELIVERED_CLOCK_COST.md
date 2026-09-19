# Delivered clock batch cost: do not adopt unconditional packing

The raw-event array saving does not predict delivered response savings. Replaying
the seven distinct socket replies from timing-clock-live-01 gives 31166 bytes
with ordinary JSONL encoding and 29912 bytes with clock_batch.py nested in the
reply's records field: 1254 bytes (4.024%) less. This proposed wire shape is an
offline experiment; existing clients expect a record list and cannot consume it.

| Reply | Records | Ordinary bytes | Packed bytes |
|---|---:|---:|---:|
| Initial observation | 2 | 4122 | 4076 |
| Initial clock | 2 | 891 | 845 |
| Entry terminal | 12 | 17761 | 16845 |
| Confirm effect | 6 | 6390 | 5996 |
| Empty final drain | 0 | 135 | 201 |
| Final evaluation | 1 | 1181 | 1222 |
| Cleanup command | 1 | 686 | 727 |

All seven full replies round-trip exactly, including cursor, status, timestamps,
request receipt metadata and ordered records. The merged initial.json caller
artifact is excluded to avoid counting its two underlying replies twice. Cleanup
is included explicitly. Byte accounting uses identical JSON encoder settings and
one newline per reply; it excludes socket overhead and filesystem formatting.

Twelve paired rounds alternate ordinary/packed order, 300 repeats of the complete
seven-reply sequence per variant. Median CPU time per reply is 20.087 versus
70.856 microseconds for encoding, and 20.718 versus 66.668 microseconds for
decoding. Median within-pair increases are 50.219 and 46.276 microseconds.
Pack/unpack's JSON-based deep copies are included. There is no warmup; raw round
samples and environment are retained. This is a local CPU measurement, not a
significance claim, live scheduling result or model latency comparison.

Decision: keep this codec offline. Unconditional wrapping enlarges empty and
single-record replies and introduces a new schema for a modest saving in this
one trace. Selective packing might avoid expansion but would require explicit
format negotiation and additional validation. It is not justified for integration
by this evidence alone. No input execution, cancellation or clock authority is
changed. Unknown clock labels remain unknown under the existing codec contract.

This trace is scripted Calc with gated evaluation. It contains no cursor gap,
mixed clock domain or cancellation case; full equality on these replies does
not prove those absent cases. Model input tokens, fees, model receipt timestamps,
live overhead, OpenTTD transfer and human-speed comparison remain unmeasured.
Future work should prioritize actual caller boundary costs and missing timing
endpoints before adding another transport format for this small byte saving.

Evidence: probe_delivered_clock_cost.py and results/delivered-clock-cost-01,
including all input/source hashes. Previous frozen raw-event studies remain intact.
