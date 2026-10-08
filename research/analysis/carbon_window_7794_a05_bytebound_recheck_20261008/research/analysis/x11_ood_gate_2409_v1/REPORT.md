# Source-bound X11 OOD distance gate

## H/T/D/C/U

- H: a simple source-bound pixel-distance gate can detect a fresh X11 visual family and fail it open to YIELD before local-model authority.
- T: use 160 base training frames as reference; threshold is the 99th percentile of non-self base nearest distances; evaluate base, prior shift, and independent fresh family.
- D: downsampled X11 raw XGetImage pixels, SHA-256 manifests, deterministic Euclidean nearest-reference distance.
- C: OOD evidence only; no semantic correctness, arbitrary GUI, token, latency, gameplay, or runtime claim. The distance gate is not authority.
- U: fresh unknowns must YIELD; production use requires semantic/effect verification and fresh corruption audit.

## Result

| set | accept | YIELD |
|---|---:|---:|
| base | 160/160 | 0/160 |
| old shift | 143/160 | 17/160 |
| fresh family | 0/160 | 160/160 |

Threshold: 0.07607. The gate cleanly rejects the fresh visual family in this fixture. This is a bounded safety result, not a promotion.
