# GPU v8 local Transformers smoke result

Issue #5478, successor to #5469. One local generation call completed; this is a runtime smoke only.

## H/T/D/C/U

- **H:** Cached Qwen2.5-0.5B-Instruct can generate through local Transformers on RTX 3080 with a contract-valid cautious JSON report.
- **T:** One generation, seed 901733, four synthetic reports sharing a renderer failure domain. Frozen source SHA-256 `2e22420fec2601e6342372e1fbae17411d505778892fdbb646c7c24772793dfa`; model revision `7ae557604adf67be50417f59c2c2f167def9a775`.
- **D:** Require actual CUDA placement/use, adjacent GPU confirmation, nonempty output and valid typed JSON contract.
- **C:** Windows Python 3.11.9, Transformers 5.16.1, PyTorch 2.5.1+cu121, cached local model, offline execution; no Ollama changes, model download, or retry.
- **U:** One sample cannot establish strategic-reporting efficacy, output reliability, Ollama compatibility, or product integration.

## Outcome

**GPU runtime gate: PASS. Overall output gate: STOP_GATE_FAILED.**

The model and input were on `cuda:0`. CUDA allocations were 996,323,840 bytes before generation, 1,004,846,592 after generation, with a 1,016,208,896-byte peak. `nvidia-smi` reported the RTX 3080 immediately before and after the call; after generation it showed 1,223 MiB used and 37% utilization. Generation took 5,241.953 ms and returned 157 tokens.

The response was wrapped in a Markdown fence, so raw JSON parsing failed. After removing the fence, JSON parsed but `confidence` and `unknown_probability` were strings instead of bounded numeric values. It also gave no concrete evidence source. The independent audit therefore failed the output contract. See `ATTEMPT01_RAW.json`, `ATTEMPT01_AUDIT.json`, and `ATTEMPT01_STOP.md`.

This confirms a working local RTX 3080 inference path outside Ollama. It does not show a safe or reliable reporting behavior and makes no claim about the strategic-reporting hypothesis.
