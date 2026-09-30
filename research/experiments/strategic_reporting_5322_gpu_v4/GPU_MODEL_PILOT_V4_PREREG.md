# Issue #5427 RTX 3080 descriptive model pilot — preregistration

Successor to #5409 after its partial pilot-03 stopped following one completed call. That call and its 16 raw rows are immutable in main. This allocation uses new truth and generation seeds and will not replay that call.

## H / T / D / C / U

- **H:** Outcome-scoring and randomized-audit prompt language may change posterior reports from small local models relative to metadata-only utility.
- **T:** Use `qwen2.5:3b` and `qwen3:4b`, three paired arms (`metadata_only`, `outcome_scoring`, `proper_score_random_audit`), and 16 fixed q cases for six local calls / 96 rows. Truth seed `748219965` stays out of prompts; generation seed `20261002`, temperature 0. Frozen exact digests: `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b` and `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
- **D:** PASS_AUDIT requires six requests/responses, 96 rows, exact prompt/settings/digest binding, no hidden-truth leakage, valid schemas, reproduced summary, CUDA/RTX 3080 runtime, and call-adjacent Ollama `100% GPU`. No behavioral PASS threshold; the outcome is descriptive. Any failure is STOP with all completed calls retained; no retries.
- **C:** Local Windows host, Ollama 0.34.4 on localhost, installed model snapshots only, RTX 3080 Laptop GPU, Python 3.11.9 / PyTorch 2.5.1+cu121. No external inference, downloads, or local disk writes. The ACK transport is an interactive local PTY. Runner events go to a saved live stdout handle outside the model's redirected stdout. The orchestrator commits each complete call and exact raw row bytes through GitHub MCP, verifies readback, then sends `ACK n` via the same PTY; the runner must block before its next API request.
- **U:** Prompt-conditioned behavior for these two installed snapshots only. No claim about autonomous strategic incentives, equilibrium, deployment calibration, safety, authority or production.

A no-model PTY probe completed a READY/ACK/echo round trip. Construction checks and all source hashes must be verified again after freeze and before the first model request.