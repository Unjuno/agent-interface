# #4106 — PNG source-raw reconstruction boundary

## H
For accepted 32-bit BGRX and XRGB buffers, the conversion to RGB PNG discards one X byte per pixel. Therefore the mapping from accepted raw bytes to PNG bytes is non-injective and `source_raw_sha256` cannot in general be reconstructed from PNG+metadata alone.

## T
Exact main `CaptureArtifacts.write`, width=height=1. For each byte order run BASE, X_CHANGED (only discarded X byte changes), and VISIBLE_CHANGED (one visible R byte changes): 6 rows, one formal invocation, no rerun/replacement/tuning. Separate stdlib PNG decoder/auditor, no X server/model/input/network.

## D
PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED iff both X-only pairs have different raw SHA256 but byte-identical PNG and RGB, both visible controls change PNG+RGB, every returned `source_raw_sha256` equals submitted raw SHA256, all process/source/evidence checks pass.

## C
This proves only non-injectivity of the declared encoder mapping. Producer-retained raw hashes may still be valid lineage assertions. It does not claim real X servers vary X bytes.

## U
No authenticity/currentness, live capture distribution, model/task/latency/token/product claim. Exact finite representation proof; no population uncertainty estimate.

## Variables / units
| symbol | meaning | SI unit | definition | domain | type |
|---|---|---|---|---|---|
| r | submitted X11 raw buffer | byte (dimensionless information unit) | four bytes for one pixel | BGRX or XRGB accepted layout | byte vector |
| f(r) | encoded PNG | byte | exact `CaptureArtifacts.write` PNG bytes | valid accepted r | byte vector |
| h(r) | source raw digest | none | SHA-256(r) | r | 256-bit value |
| p(r) | decoded RGB | byte | stdlib PNG reconstruction | RGB8 1x1 | 3-byte vector |

Dimensional check: all equality gates compare bytes/digests or integer pixel extents; no incompatible physical units are combined.
