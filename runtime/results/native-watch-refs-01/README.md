# Lossless references across native sensor observations

The existing compact presenter referenced exact copies of the final observation.
A visual watch also duplicates a different capture between its last observation
and sample history. This update can reference those copies within the same
response without removing the complete observations or their event history.

## Interface

`compact_native_receipt` compares full, legacy v1 and new v2 representations using
canonical UTF-8 JSON byte length, and chooses the smallest. The existing opt-in
`agent_exchange.py --native --review compact` and `agent_review.py --native
--compact` use it. Full mode is unchanged.

V2 carries an explicit source-path to target-path map. Every target remains a
complete observation in the response, and the top-level final observation stays
complete. Only listed paths are references; literal reference-shaped user data
is retained. Expansion refuses chains, overlap, malformed pointers, altered
markers and attempts to replace the top-level observation. Existing v1 expansion
remains supported; v2 consumers must use the updated expander or interpret the
declared v2 map. Already projected/caller-metadata-bearing views are not rewritten.

Deduplication requires exact serialized equality of the entire observation,
including sequence, capture time, binding, image path/hash and unknown fields.
Identical pixels from different captures are not interchangeable. Watch states,
false-to-true events, unknown conditions, failures and release evidence remain.
The source report hash still names the authoritative raw artifact; projection
and successful expansion alone do not authenticate an independently tampered view.

## Primary-assistant use

Fresh private WSL/Xvfb Inkscape seed 991098: the primary assistant viewed the exact
source image, selected the red object, moved it with 15 Right chords and saved.
It received the actual v2 compact reply and image, observed x=80 and explicitly
finished at stage 2. One native program completed with verified neutral release.
The watch reported 3247 changed pixels in the object region and zero in blank
paper. Independent SVG parsing confirms x=80 from x=50, y=50, width=40, height=30.
Teardown processes were terminal. No helper model or Docker allocation was used.

## Same-receipt size comparison

All three projections use the identical raw reply. The old implementation is
retained from the exact base Git blob under source/baseline_receipt_references.py.
Canonical compact JSON sizes (not pretty-printed artifact file sizes):

| Representation | Receipt metadata bytes |
|---|---:|
| Full | 10,132 |
| Previous compact | 9,633 |
| New compact | 9,004 |

This saves 629 metadata bytes, 6.53% versus previous compact. The same PNG is
55,371 bytes, or 73,828 base64 bytes; including that unchanged base64 payload
reduces the relative difference below 1%. These byte counts are not model input
tokens, billed image tokens, latency, or a matched model-utility result. The actual
primary-model usage remains unavailable.

A subsequent fixed same-receipt cost check ran 10 warmups per arm, then 100 pairs
with alternating order, using the retained old/new source in one WSL process.
Projection-only median was 0.822 ms previous versus 1.579 ms new; p95 was 1.445
versus 2.911 ms. Thus the smaller representation costs about 0.757 ms more at
the median in this local check. `projection-cost.json` retains all 200 timings
and `measure_projection.py` the command. No model, image rendering, network or GUI
was included. This is an explicit size/cost tradeoff, not end-to-end improvement.

30 focused reference/presenter/exchange tests pass. New controls cover multiple
captures, complete error/unknown-state preservation, literal reference shapes,
pointer escaping, idempotent projection, caller metadata, chains/markers and
invalid array indices. The original small-report fallback is retained.

`audit.py` independently reconstructs the full receipt from the explicit map,
checks source/request/reply and image hashes, verifies the actual presented view,
recomputes byte sizes, parses the saved SVG and checks terminal cleanup. Source,
raw run, client decisions and returned metadata (without duplicate base64) are
retained. The earlier visual-watch release failure remains unchanged in its own
archive; this successful run does not explain it or prove it repaired.

```sh
python3 runtime/results/native-watch-refs-01/audit.py
```
