# GPU pilot-01 preflight STOP

The frozen pilot runner made **zero model calls**. It queried local Ollama inventory, then stopped on an exact digest mismatch for `qwen3:4b`, as required by the frozen runner. The captured `calls.json` is empty, and `raw.jsonl` is empty. No responses or research outcomes are claimed. No retry was made.

- Expected by frozen pilot source: `359d7dd4bcda3b86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`
- Observed from Ollama `/api/tags`: `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`
- `qwen2.5:3b` matched its frozen digest.
- Local preflight: Ollama 0.34.4, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA available, NVIDIA GeForce RTX 3080 Laptop GPU.
- The in-memory capture adapter's source hash and the frozen pilot/auditor/preregistration hashes were verified before allocation.

This is a STOP before inference, not a negative or positive model result. The version-1 allocation is closed. Any test using the observed digest requires a successor preregistration and new allocation; do not edit these frozen files or reuse this allocation.
