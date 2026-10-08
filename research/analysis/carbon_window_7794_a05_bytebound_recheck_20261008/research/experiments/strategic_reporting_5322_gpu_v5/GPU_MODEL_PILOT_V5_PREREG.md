# Issue #5434 RTX 3080 model pilot v5 — preregistration

Successor to #5427. The earlier v4 GPU allocation has an immutable STOP with unknown consumption and no recoverable response. This allocation uses fresh seeds and does not replay or pool earlier attempts.

## H / T / D / C / U

- **H:** Outcome-scoring and randomized-audit instructions may change prompt-conditioned posterior reports from small local models relative to metadata-only utility. Exploratory and descriptive only.
- **T:** `qwen2.5:3b` and `qwen3:4b`; three arms (`metadata_only`, `outcome_scoring`, `proper_score_random_audit`); 16 fixed cases; six calls total; 96 rows; temperature 0. Truth seed `748219966`; generation seed `20261003`. Truth labels remain absent from model prompts. Digests: Qwen2.5 `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`; Qwen3 `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
- **D:** Independent audit requires the exact six request/response records and 96 rows, matching prompt/settings/digests, no truth leakage, valid schema, reproducible descriptive summary, CUDA/RTX 3080 runtime, and call-adjacent Ollama `100% GPU` placement. There is no behavioral pass threshold. Any failure is STOP; no retries or replay.
- **C:** Local Windows host, localhost Ollama only, installed model snapshots only, NVIDIA RTX 3080 Laptop GPU. No downloads, external inference, or local disk output. The exact v5 runner passed a six-call synthetic PTY smoke: per-call event framing, readback from GitHub before each ACK, final framed status, and clean exit. Each call event is bounded to 78-character ASCII lines with length/SHA-256 and ordered chunks; frame ID 0 is reserved for final status. The runner verifies the frozen source digests before either smoke mode or inference. Each real model call must be followed by GitHub commit and exact readback before the next call starts.
- **U:** Findings apply only to these fixed prompts, seeds, and two installed snapshots. No claim about autonomous incentives, deployment calibration, equilibria, safety, authority, or production.

Inference is authorized only from the immutable source set in `GPU_PILOT_FREEZE_V5.json`, after rereading that freeze. A failed capture, invalid frame, failed GitHub readback, or missing ACK stops the allocation without retry.
