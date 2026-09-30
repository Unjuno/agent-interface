# Issue #5409 RTX 3080 descriptive model pilot — preregistration

Successor to #5397 after the previous runner's final in-memory output was lost. The earlier allocation is unverified and will not be replayed. This is a fresh allocation with new truth and generation seeds.

## H / T / D / C / U

- **H:** Outcome-scoring and randomized-audit prompt language may change small local models' posterior reports relative to metadata-only utility.
- **T:** Run `qwen2.5:3b` and `qwen3:4b` on 16 fixed posterior cases in three paired arms (`metadata_only`, `outcome_scoring`, `proper_score_random_audit`): six total local calls and 96 case rows. Truth labels use RNG seed `748219964` and remain hidden from prompts. Every call uses temperature 0, generation seed `20261001`, and the frozen JSON schema. Exact installed digests are `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b` and `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
- **D:** PASS_AUDIT requires exactly 6 requests/responses and 96 raw rows; exact prompt pairing, seed/digest binding, no truth leakage, valid schemas, reproducible summary, RTX 3080/CUDA evidence and `100% GPU` Ollama placement. There is no behavioral PASS threshold: this pilot is descriptive. Any mismatch, unsupported response, model/runtime error or audit error is STOP; do not retry.
- **C:** Local Windows host, Ollama 0.34.4 at localhost only, already-installed models only, RTX 3080 Laptop GPU, Python 3.11.9 / PyTorch 2.5.1+cu121. No model downloads, external inference, or local disk writes. After each completed model call, persist the response, runtime evidence and its 16 rows through GitHub MCP before proceeding to the next call.
- **U:** Prompt-conditioned behavior for the two installed model snapshots only. No claim about autonomous strategic incentives, deployment calibration, equilibrium, safety or authority.

The local capture controller must retain each completed call durably before a subsequent call starts. The independent auditor runs over the concatenated raw call records and rows after the six calls. Freeze every source hash and exact procedure before the first call.