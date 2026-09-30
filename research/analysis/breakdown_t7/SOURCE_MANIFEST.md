# T7 source and runtime manifest

Issue #5444 preregistration comment: `5910699630`.

| file | SHA-256 |
|---|---|
| `experiment.py` | `73affba3041088cf1e80bbe7c90730ee204b902548ced640872c6e0ab70e4115` |
| `audit.py` | `16e16b9011f35eff6d3744d807a310fc75b64a5976ebc810b50fc1e3ebb0a4f8` |
| `corruption_controls.py` | `86a1e968d8e7409c49452b31d7b30808450d7e446345d1c29fe58ba915dcb300` |

- OrbStack Docker Engine `29.4.0`, `linux/arm64`.
- `python:3.12-slim`, local image ID and repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Network disabled for formal run, audit, and corruption controls.
- No randomness, downloaded data, or external services.
