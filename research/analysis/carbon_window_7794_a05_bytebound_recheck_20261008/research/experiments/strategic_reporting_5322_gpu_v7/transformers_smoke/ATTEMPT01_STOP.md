# Attempt 01 STOP — Transformers API return-shape mismatch

The frozen experiment source (SHA-256 `b51c384947b955f3dd22a0b4470dcfaff7224cf8e40c0a6abc4a3dd11f131331`) ran once, offline, with exit code 1. It loaded all 290 weight tensors and reached the line after `model.to("cuda:0")`. It then stopped before generation because Transformers 5.16.1 returned a `BatchEncoding` from `apply_chat_template(..., return_tensors="pt")`; the runner incorrectly accessed `tokens.shape` instead of `tokens["input_ids"].shape`.

**No `model.generate()` call occurred; inference_calls=0.** The JSON contract and call-adjacent GPU gates were not evaluated. The raw output/exception summary is retained in `ATTEMPT01_RAW.json`. Do not relabel this as a GPU inference PASS and do not rerun this frozen allocation. Any correction must be a new successor with a fresh source/seed and frozen gate.
