# GPU v8 one-call Transformers smoke test (Issue #5478)

A new source/seed allocation after #5469's pre-generation STOP. This run tests only local CUDA runtime readiness.

## H/T/D/C/U

- **H:** One deterministic cached Qwen2.5-0.5B-Instruct generation can use RTX 3080 and return a contract-valid cautious JSON report when BatchEncoding is indexed through input_ids.
- **T:** Execute gpu_smoke.py exactly once. Fresh seed 901733. Four seeded synthetic reports share a renderer failure domain; the model must preserve the dependency limitation. Frozen source SHA-256: 2e22420fec2601e6342372e1fbae17411d505778892fdbb646c7c24772793dfa. Explicitly access encoded["input_ids"].to("cuda:0") and perform one generate call only.
- **D:** Require nonempty generation, model/input on cuda:0, nonzero CUDA allocated/peak bytes, nvidia-smi identifying the same RTX 3080 before loading, adjacent before/after generation, and valid JSON with required fields plus bounded confidence and UNKNOWN probability. Otherwise STOP; no retry.
- **C:** Windows Python 3.11, Transformers 5.16.1, PyTorch 2.5.1+cu121, cached model snapshot 7ae557604adf67be50417f59c2c2f167def9a775. Offline mode, no C: writes (zero bytes free), no model download, Docker/WSL, Ollama changes, or external API.
- **U:** One readiness call cannot support a behavioral or incentive-compatibility result, repeated reliability, Ollama compatibility, or Agent Interface integration.

