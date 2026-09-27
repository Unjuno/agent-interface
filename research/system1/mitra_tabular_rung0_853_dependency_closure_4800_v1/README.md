# Mitra dependency-closure successor evidence (#4800)

This package preserves the immutable #4745 exact-lock STOP and records an additive offline dependency-closure ladder. It does not claim CUDA inference, model quality, or performance.

## H / T / D / C / U

- **H:** the direct AutoGluon `MitraClassifier` entry point may become importable on the pinned Python 3.11 CUDA image after adding its runtime dependency closure, without changing the model revision or fixtures.
- **T:** the exact original 59-wheel #4745 lock was retained unchanged. Successor revisions added only hash-pinned distributions. Each gate ran with Docker `--network none`; the base image was `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, image ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
- **D:** rev1 stopped at missing `loguru`; rev2 stopped at missing `einops`; rev3 stopped at missing `einx`; rev4 installed all five added packages and imported `MitraClassifier` successfully. The independent raw-only audit is in `audit.py`.
- **C:** no model was constructed, no checkpoint was deserialized, no fit/predict/forward was called, and no CUDA device was requested. These outcomes measure dependency/import readiness only.
- **U:** CUDA forward compatibility, placement, output ABI, reread behavior, and latency remain unknown. The separate #4792 run has completed and its owner released the RTX 3080. #4471 reports `STOP_FORMAL_RESULT_SERIALIZATION_NAMEERROR_AFTER_TRAINING`; it is not an active run. Recheck local processes, containers, open allocations, and device memory immediately before any separately preregistered Mitra GPU invocation.

## Exact evidence

`EVIDENCE.json` pins byte length and SHA-256 for each raw artifact. Each `.raw.b64` file carries those exact original bytes; decode by base64 and compare SHA-256. `SOURCES.json` records PyPI file URLs/digests and observed license metadata for the five added distributions. The ANTLR source distribution produced a disposable wheel inside the offline container; that derived wheel was not retained or asserted reproducible.

The original 59-wheel acquisition manifest and STOP audit remain at `research/system1/mitra_tabular_rung0_853_dependency_stop_v1/` on main. Successor wheelhouse manifests enumerate filenames, byte lengths and upstream SHA-256 values; package archive bytes are not duplicated in this repository.

Run the standard-library-only audit in a pinned Python 3.12 helper image with networking disabled:

```sh
docker run --rm --network none --read-only --cpus=1 --memory=512m --pids-limit=64 -v "$PWD:/evidence:ro" -w /evidence python:3.12-slim-bookworm python audit.py
```
