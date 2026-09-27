# Mitra-v2 CUDA dependency-closure STOP — Issue #4745

This additive evidence package records a setup STOP before the preregistered GPU allocation. It does not edit the exact #4745 freeze, earlier comments, closed PR #4777, or the original #853 CPU STOP.

## H — question

Can the exact pinned Python 3.11 CUDA image dependency lock import the preregistered direct `MitraClassifier` entry point offline, before loading any model weights or making any inference call?

## T — observed procedure

- Base image: `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, local image ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
- Immutable frozen lock SHA-256: `d871eb53e8ed38d5ee5d2c8fbae8ed0b2a3f265523bbf24b0573f42b17864ec9`; its source remains the exact #4745 `requirements.lock`.
- Frozen wheel manifest SHA-256: `158297ee664e598b0648970eb9b630dce7055f0fa75f2ce85a0bb8d700e2e48b`.
- Acquired and checked 59 wheels, total 195,307,446 bytes; all file digests and lengths equal the frozen manifest. `ACQUISITION_PROVENANCE.json` records package/version, exact PyPI API, upstream file URL, digest, and wheel metadata license evidence. Its SHA-256 is `6af75de734b1e505935a5e993a905acbc28e7910dbd8e2efeb70c21d3ce3d8`.
- A first acquisition attempt stopped when its container `/tmp` tmpfs filled; no model or GPU action occurred. A distinct `wheelhouse-attempt02` completed and is the source for the retained exact log.
- With networking disabled and no GPU device request, pip installed the exact lock successfully (`OFFLINE_INSTALL_EXIT=0`). The direct import reached AutoGluon's Mitra module but stopped at `ModuleNotFoundError: No module named 'omegaconf'`.
- Raw log SHA-256: `85fbafaf2397165491b9b6eaaf3445d40c7cb77ec687cb5d342a8f10ce7a8f2f`.
- GitHub text storage normalizes line endings. To retain the exact original lock, wheel manifest, and raw-log bytes independently of that display normalization, byte-exact base64 envelopes are also stored as `requirements.lock.raw.b64`, `wheelhouse-manifest.json.raw.b64`, and `offline-install-import-preflight.log.raw.b64`. The auditor verifies their hashes and checks normalized text against each envelope.
- No checkpoint was mounted or loaded; zero fit, prediction, optimizer, formal rows, or GPU invocations occurred. The unrelated Ollama container was not touched.

Earlier #4745 comments record a distinct construction install/import probe in which another Mitra module imported. This STOP is narrowly about the exact frozen lock and direct `sklearn_interface.MitraClassifier` import path captured by this log. It does not claim that no repaired closure can work or that CUDA forward is incompatible.

## D — disposition

`STOP_LOCAL_ARTIFACT_OR_RUNTIME`: the exact frozen requirements closure is insufficient for the preregistered import path. Formal GPU execution was not started; no model/runtime-performance hypothesis outcome is available. Preserve the lock, wheel manifest, and first attempt unchanged. Any repair must use a new successor allocation, new frozen closure and evidence path.

## C — alternative explanations

The separate earlier package installation may have had `omegaconf` transitively installed; the current lock was reduced to added packages relative to the base and omitted a runtime import dependency. This is a package-closure defect, not evidence about GPU model execution. The target import may require additional dependencies after OmegaConf, so adding one package alone is not presumed sufficient.

## U — scope

One local base image and one exact dependency lock/import gate. No weights, CUDA device, model quality, latency, training, or product/runtime claim.

## Reproduction and audit

Run `python audit_stop.py` in this directory. It uses only Python standard library and verifies pinned identities, artifact count/bytes, acquisition provenance, and the expected raw import failure. Three mutation controls (missing failure, altered manifest, failed pip-install marker) were rejected locally. The same raw-only audit passed in a read-only, network-disabled `python:3.12-slim-bookworm` helper container, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; this helper did not build or run the CUDA model image.


