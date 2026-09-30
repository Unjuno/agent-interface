# Issue #4871 — frozen-input integrity STOP

Disposition: `STOP_CORPUS_HASH_MISMATCH`. No model load, forward, precision comparison, fit, formal timing, or runtime action occurred.

## H/T/D/C/U
- H: Changing arithmetic precision may alter selected-code shared-prefix numerical drift on the unchanged #4623 excluded rows, without reopening the earlier FP16 FAIL.
- T: Newly registered construction-only successor #4871 (`typed-readout-precision-boundary-1014-v3-20260927`); branch `research/typed-readout-precision-boundary-1014-v3-20260927`; required exact local model and corpus SHA verification before any model use.
- D: `STOP_CORPUS_HASH_MISMATCH` before model load.
- C: The existing STOPs #4623 and #4639 remain immutable; no formal 1,024-question block and no numerical tolerance change.
- U: The exact artifact version intended by the #4871 issue body must be resolved by a separately documented allocation/edit before continuing.

## Evidence and checks
- Parent main at allocation: `88497cf7e90bda6c99e951654c19bf247be4c6e4`.
- Exact model revision `7ae557604adf67be50417f59c2c2f167def9a775` is locally cached. Its `model.safetensors` SHA-256 is `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`, matching `MODEL_MANIFEST.json`. Config/tokenizer file hashes and sizes also match that manifest.
- Pinned image ID `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`; package versions PyTorch 2.5.1+cu121, Transformers 5.16.1, safetensors 0.8.0.
- Host and this pinned container both identify `NVIDIA GeForce RTX 3080 Laptop GPU`. GPU usage was 0 MiB/0%; existing Ollama container was left running and untouched. This verified eligibility only; no model forward ran.
- GitHub Git Blobs API read exact committed `corpus.jsonl` bytes from main path `research/system1/typed_readout_prefix_gpu_1014_v1/corpus.jsonl`, blob SHA `4287a61f6194f39a3062696c84c1f9907ff1ece1`, size 270,228 bytes. Independent local SHA-256: `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.
- Main `SOURCE_MANIFEST.json` and `#4639` issue comment instead assert raw corpus SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c` for the same path. The Git blob hash and raw-byte hash are independently reproducible but differ. No suffix corpus rows were read into a model execution. We did not normalize line endings, regenerate, or select a substitute.
- The GPU container check transiently failed once to find the driver, then passed on an immediate read-only retry; subsequent host and container checks both saw the RTX. No persistent CUDA/driver problem was found.

## Stop rule
The issue requires the exact source corpus hash to be verified before rows/model use. Because the committed bytes contradict the declared raw-file SHA, stop without trying another representation or historical blob. Preserve this evidence and prior #4623/#4639 outcomes unchanged. A future allocation may resolve which corpus version is authoritative, then allocate a fresh construction test with an exact pre-load hash gate.
