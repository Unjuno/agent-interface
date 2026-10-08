# T0 source and runtime manifest

Issue #5410 preregistration: comment `5911036464`.

| file | frozen SHA-256 |
|---|---|
| `experiment.py` | `a136e0f92591140220c8d0d8f8ba2cdaf0456947b5f9f9e7838a6a0bb17e9e9a` |
| `audit.py` | `220ff8b1145f5487047406dc1837e172f0f633c6bcec6fc5ae5abebf0086dcdb` |
| `corruption_controls.py` | `2ed2faaab53925d6b505e63dcdc3ef164d00c419d85965c58f7db58869943f41` |

- Frozen base: main `6a1e2f16762b1a2ace7347a282f7ad6d12c7a0fe`.
- OrbStack Docker Engine `29.4.0`, `linux/arm64`.
- Image `python:3.12-slim`, local ID and repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Formal command has `--network none`; no randomness or external data.
