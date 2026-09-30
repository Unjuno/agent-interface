# Issue #4875 — construction STOP record

Disposition: `STOP_OUTPUT_NOT_EMPTY`. The single frozen Docker invocation exited 1 before loading the model or issuing any model forward. No retry was made, as required by Issue #4875.

## H / T / D / C / U

- **H:** FP32 or BF16 may reduce shared-prefix-cache selected-answer-logit drift on nine fixed, previously excluded pairs without changing any of the eight winners.
- **T:** One frozen construction command on pinned CUDA image `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`, exact Qwen model and exact 85b5 corpus, using B00/B17/B63 × slots 0/7/15 across FP16/BF16/FP32.
- **D:** `STOP_OUTPUT_NOT_EMPTY`, raised at runner precondition line 83. The host command redirected container stdout/stderr into files under the same mounted `/out` directory before launching the container; the runner therefore correctly refused the already-populated directory before hashing/loading the model.
- **C:** No model weights were loaded, no forward/generation/training occurred, no optimizer step occurred, and no formal rows/timings were produced. The existing Ollama container was left running and unchanged. GPU returned to 0 MiB / 0% after exit.
- **U:** Precision/cache equivalence remains untested. The scientific question is unresolved; this invocation yields no precision result.

## Frozen identities and invocation evidence

- Issue #4875 allocation: `typed-readout-precision-boundary-1014-v3-successor-20260927-01`.
- Parent main at allocation: `88497cf7e90bda6c99e951654c19bf247be4c6e4`; the pre-run main check was `cd7853030248c0d19293bf573cd7c90109b1a57e`, whose single new commit added disjoint GTK experiment evidence files only.
- Branch: `research/typed-readout-precision-boundary-1014-v3-successor-20260927`; final source freeze was read back from this branch before invocation.
- Corpus: 270,292 bytes, SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`.
- Model revision: `7ae557604adf67be50417f59c2c2f167def9a775`; weight SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Image: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`; container reported `RuntimeError: STOP_OUTPUT_NOT_EMPTY` at `/src/run_construction.py`, line 83.
- Exactly one invocation; Docker exit 1; stdout 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr 245 bytes, SHA-256 `ff4ddd19f26e779ab8b91829c1c8df24d8d42a46e5cd82677f95ff0dcea59c22`.
- The only output-directory files are `runner.stdout.txt` and `runner.stderr.txt`; no `result.json` or audit output exists. These host-side log files caused the guard to stop, and their hashes are retained above.

## Gate result

The STOP is an invocation/output-path setup failure, not an ML or numerical outcome. Do not retry or relabel this allocation. Any future attempt requires a separately authorized successor allocation with host logs directed outside the fresh mounted model-output directory. Preserve #4871's corpus-identity STOP and all #4623/#4639 results unchanged.