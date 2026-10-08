# Qwen constrained intent diagnostic — Issue #4856

## Preflight outcome

`STOP_PREMODEL_ARTIFACT_HASH_MISMATCH`. The exact adapter required by the preregistered comparison could not be verified. Predecessor `fit.json` records SHA-256 `c51dcfff55254b43559a8d02a831707fe309080d5fd958a44bef2d431f2f0f84`; the binary at the stated path on checked main `e5c88df05f6b43e39e5a99441562841c52a2b5d7` hashes to `c35c7172f5e97fa45df73066e2f77f565741562172f2ae719c8aad9361553997`. Its GitHub blob SHA `1008520f5fd3874eb51275fde8f4b4c87870f51c` matches the repository file fetched from that ref. The config hash also differs; see `PREFLIGHT_STOP.json`.

No model call, model fit, formal row generation, retry, or substitution occurred. This is a provenance STOP before scientific exposure, not a result for or against the constrained-decoding hypothesis. Do not modify #4792 or silently use the mismatched artifact. Resume only if the exact predecessor adapter can be independently recovered and its expected hash verified, or preregister a different scientific question with a genuinely new model artifact.

