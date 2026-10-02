# Issue #6048 — terminal preflight receipt STOP

Allocation: `5478-json-format-gpu-6048-01-20261001-01`  
Owner: `01a0b990-3d17-72f1-a908-9a2072104ce5`  
Frozen main: `cc804427c14a5c98370b84f9d63809cb5ca0c0ca`

## H / T / D / C / U

- **H:** One deterministic local RTX 3080 generation from the unchanged cached Qwen2.5-0.5B-Instruct model, with an explicit JSON-only prompt, will emit one response satisfying the frozen strict JSON contract.
- **T:** One fresh synthetic input (seed `901734`), one frozen prompt, one local greedy generation, followed only on candidate exit 0 by one independent CPU raw auditor. No retries or substitute settings.
- **D:** Scoped output pass requires the raw response itself to parse as the exact JSON contract with contemporaneous local RTX 3080 placement. Any pre-model failure is terminal STOP / not evaluated.
- **C:** Windows host, exclusive RTX 3080 slot 13:20–13:40 UTC; no Docker/WSL/container, download, network, fine-tuning, adapter, or package install.
- **U:** A single synthetic prompt-format case; not semantic correctness, reliability, calibration, or fine-tuning evidence.

## Result

**`STOP_PREFLIGHT_RECEIPT_SCHEMA_MISMATCH / NOT_EVALUATED`.** The one preflight exited 0 and recorded no gate errors, but its persisted `PREFLIGHT.json` lacks the `receipt_written` property. The preflight's console summary says `receipt_written: true`; `generate_one.py` independently requires that property in the saved JSON. The one candidate-wrapper invocation therefore exited 1 with the preserved stdout `STOP: preflight failed; no model load` before importing PyTorch or Transformers.

Counts: preflight 1; candidate wrapper 1; model load 0; CUDA initialization/calls 0; generation 0; auditor 0; retries 0. Since candidate exit was nonzero, the frozen protocol's auditor condition was not met and the auditor was not invoked. No scientific output was produced.

The original preflight receipt is retained unchanged at [`PREFLIGHT.json`](PREFLIGHT.json), SHA-256 `8bf8085df3db7327adc0f5015031b6ed020e80bf85f249c6e009d9631d677739`. It records RTX 3080 Laptop GPU, 16 GiB total, 0 MiB used / 0%, no compute processes, 4,462,030,848 free disk bytes, and the frozen input/model/tokenizer/source digests. No container or WSL workload was used.

The allocation is consumed; the remainder of its GPU window was released immediately in #5085 comment [5932427504](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5932427504). **No retry or code repair was run under this allocation.** Any future attempt would need a distinct successor allocation, new lease, and fresh preregistration.
