# GPU v7 local Transformers smoke result

Issue #5469; successor to #5455. This is a one-run local readiness probe. It does not test strategic-reporting behavior and does not modify Ollama.

## H/T/D/C/U

- **H:** A deterministic generation through the cached Qwen2.5-0.5B-Instruct Transformers runtime can produce a contract-valid advisory JSON report on RTX 3080.
- **T:** One run, seed 682731, frozen script SHA-256 `b51c384947b955f3dd22a0b4470dcfaff7224cf8e40c0a6abc4a3dd11f131331`; model snapshot `7ae557604adf67be50417f59c2c2f167def9a775`.
- **D:** Require successful nonempty generation, cuda placement and memory evidence, pre/post RTX 3080 identification, valid JSON contract.
- **C:** Windows Python 3.11, Transformers 5.16.1, PyTorch 2.5.1+cu121, offline cached 0.5B checkpoint. Host C: had zero free bytes; exact frozen source was executed from memory. Docker Desktop/WSL did not answer bounded CLI probes.
- **U:** One smoke run cannot establish behavior quality, repeatability, Ollama compatibility, or product integration.

## Outcome

**STOP_BEFORE_GENERATION.** The model loaded (all 290 tensors) and the runner advanced beyond `model.to("cuda:0")`. It then accessed `tokens.shape`, but Transformers 5.16.1 returned a `BatchEncoding` from `apply_chat_template(..., return_tensors="pt")`. The runner exited 1 before `model.generate()`; inference call count is zero. Output contract and call-adjacent GPU gates were not evaluated.

The raw runtime/exception summary and STOP record are `ATTEMPT01_RAW.json` and `ATTEMPT01_STOP.md`. This frozen source was not retried. It is not a GPU inference result; a corrected probe needs a new successor with a new source/seed and preregistered gate.
