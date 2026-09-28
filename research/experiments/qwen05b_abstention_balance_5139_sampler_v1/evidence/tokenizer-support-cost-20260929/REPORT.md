# #5139 offline tokenizer-only support cost characterization

Date: 2026-09-29. This is an additive CPU-only construction/preflight observation, not a formal model allocation.

## H / T / D / C / U

**H.** Although both support arms contain 32 rows, their actual tokenizer input budgets may differ due to different semantic-class composition and row content. Measure tokenized raw prompt and target lengths on the immutable construction dataset before treating equal row count as equal token exposure.

**T.** From the repository root, ran PowerShell:

```powershell
$snapshot = Join-Path $env:USERPROFILE '.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775'
python -B research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/tokenizer-support-cost-20260929/tokenizer_support_cost.py --snapshot $snapshot
```

The script verifies SHA-256 of `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, and `merges.txt` against the published #5139 asset manifest, loads only `tokenizers.Tokenizer.from_file`, regenerates construction sentinels formal `903520260929` / support `903520260930`, checks exact canonical dataset SHA-256 `d96c4072db2ee3bb1af7503a8ae98e062794072385a15099f32121a7a8caad4b`, and runs the independent support-selection auditor. It encodes raw prompt and target separately with `add_special_tokens=False`; no chat wrapper or trainer path is assumed.

**D.** Exit 0, `PASS_TOKENIZER_ONLY_SUPPORT_COST_CHARACTERIZATION`. Every tokenizer file hash matched. The independent support audit was clean. Each arm had 32 rows and all 32 prompt strings round-tripped exactly. Balanced arm: 4,566 prompt + 389 target = **4,955 raw tokens**, max per-row prompt+target 258. Imbalanced arm: 5,821 prompt + 598 target = **6,419 raw tokens**, max 264. Thus balanced used **21.56% fewer raw prompt tokens** and **22.81% fewer prompt+target tokens** in this one frozen synthetic construction sample. Full class-by-class counts, hashes, and values are in `result.json`.

**C.** Same raw dataset, same locally hashed tokenizer assets and implementation (`tokenizers` 0.23.1), 32 rows per arm, independent support selection audit, exact prompt decode roundtrip. No seed search or row substitution.

**U.** This is a single synthetic support sample and raw-string tokenization only. It does not measure trainer serialization, chat template/special tokens, padding, packing, truncation, model loss, optimization steps, GPU memory/time, or quality. The local tokenizer package version is not the not-yet-frozen formal container environment. The token gap is a real budget imbalance in these two sampled arms, but it is not independently causal evidence for quality; any token-matched comparison would need a separately preregistered design rather than post-hoc changes to this allocation. No model weights, tokenizer wrapper, CUDA/GPU, Docker/OrbStack, fit, or adapter were loaded or used.
