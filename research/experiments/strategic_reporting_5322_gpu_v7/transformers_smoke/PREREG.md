# GPU v7 one-call Transformers smoke test (Issue #5469)

This is a single local runtime/readiness allocation after Ollama's CPU fallback. It does not test strategic-reporting efficacy, compare models, modify Ollama, or download weights.

## H/T/D/C/U

- **H:** One deterministic Qwen2.5-0.5B-Instruct generation through local Transformers can run on the RTX 3080 and produce a contract-valid cautious JSON advisory report.
- **T:** Execute `gpu_smoke.py` exactly once. Fresh seed: 682731. Frozen source set is the synthetic three-report scenario generated from that seed. Freeze model, prompt construction, source, hashes and gates before execution. Do not retry.
- **D:** PASS only when local model identity and exact script hash are captured; the one call returns nonempty tokens; model and inputs are on cuda:0; CUDA allocated and peak allocated bytes are nonzero; before-call and after-call nvidia-smi both identify the RTX 3080; generated output is valid JSON with all required keys and bounded confidence/unknown_probability. Any failed check is STOP_GATE_FAILED / STOP and must be retained unchanged.
- **C:** Windows host Python 3.11, Transformers 5.16.1, PyTorch 2.5.1+cu121, CUDA 12.1, existing cache snapshot `7ae557604adf67be50417f59c2c2f167def9a775`. Docker Desktop and WSL CLI did not respond during bounded probes. C: has 0 bytes free, so do not write local files; execute the frozen GitHub source from memory. No model download, external API, Ollama mutation or restart.
- **U:** A single small-model generation establishes only a local GPU runtime path. It says nothing about model behavior quality, incentive compatibility, repeated reliability, Ollama, or Agent Interface integration.

Frozen experiment script SHA-256: `b51c384947b955f3dd22a0b4470dcfaff7224cf8e40c0a6abc4a3dd11f131331`.
