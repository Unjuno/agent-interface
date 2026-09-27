# Successor #4861 — recovered exact-adapter diagnostic

This is an additive, one-shot diagnostic package. It does not alter #4792/#4803, #4856/#4858, or the trie-construction-only #4854 result. See Issue #4861 for the complete H/T/D/C/U and immutable lineage.

- Allocation: `qwen-intent-grammar-4792-recovered-20260927-02`
- Intake main: `da3a8e93d426dd7af803776b51583835678f6c00`; publication main advanced to `f44ee126017520659bc838c6149ce17dd45a94af` during preparation.
- Branch: `research/qwen-intent-grammar-4792-recovered-v2`
- Path: `research/experiments/qwen_intent_grammar_4792_v2/`
- Fresh data: `make_rows(4792962, "heldout", 32)`; never reuse seed 4792961 from #4856 or #4792 formal rows.
- Model: cached Qwen2.5-0.5B-Instruct snapshot `7ae557604adf67be50417f59c2c2f167def9a775`; seven-file SHA-256 map is in `formal/src/FREEZE.json`.
- Adapter: exact recovered #4792 fit.json bytes, 2,175,168-byte weights and 701-byte config; hashes in freeze. Historical `/model` path is handled through a temporary runtime alias; committed files stay exact.
- Runtime: local cached Docker image `qwen05b-action-sft:build01`, ID `sha256:63ce8205b5e0cf7daddac087d6c1bd5489d51e3af345cf923af925026bdd600c`, linux/amd64; CPU only, float32, 2 intra-op / 1 inter-op threads, eager attention, greedy, 48-token cap, one model load, zero fit, offline, no retries.
- Candidate set is state-only. Same inputs/prompts/model/adapter/settings in free and constrained arms; trie token mask is the only difference.
- Pass gates: full independent audit, 8/8 corruption controls rejected, constrained canonical candidate JSON 32/32, zero unsafe/mismatched effects, constrained exact intent >=70%, paired gain >=20 percentage points. Otherwise retain FAIL/STOP/HOLD.

## Compact evidence policy

The repository receives only source, freeze, protocol and exact ~2.18 MB adapter/config. The 988 MB base model, cache, Docker image and generated per-row input/raw output stay on the PC. The result index/PR will report their local bundle path, SHA-256, byte counts, row/call counts, audit summary, terminal state and exact invocations. This keeps GitHub handoff lightweight while preserving local full auditability.

## Execution boundary

Construction tests and hash/tokenizer checks do not load the causal model. Formal input is generated exactly once only after this package is byte-read back from this branch. Paired inference runs once in a fresh output directory. A separate raw-only CPU audit and eight copy-only corruption controls follow. Any preflight, execution or audit failure is terminal; no retry or tuning. Exact PowerShell commands and resource caps are retained in the local bundle's `PREREGISTRATION.md`.
