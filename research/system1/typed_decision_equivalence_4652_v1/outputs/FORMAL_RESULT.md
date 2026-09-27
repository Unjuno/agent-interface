# Formal result — Issue #4652

**Decision: `PASS_TYPED_DECISION_EQUIVALENCE_1024`.** The one frozen formal allocation and its separate independent GPU audit both completed. All 1,024 paired typed-answer decisions matched; the raw-only independent audit returned `errors: []`. This is a categorical execution-mode result only: it does not waive #4639's score-tolerance STOP, establish semantic accuracy, or support a latency/speed claim.

## Frozen execution

- Branch: `research/typed-decision-equivalence-4652-v1-20260927`; main intake `27c7f38c9bb072e0462b07edd06d6cf9ef46bb0a`.
- Freeze revision 2 SHA-256: `70e0a4c4aa1e8123e4f4c8e691624b433953df255811ab79f2f357c69346c337`.
- Exactly one formal invocation; supervisor returned 0 with 1,024 durable rows in 85.5 seconds. No retry or exclusion.
- Local Docker image ID `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`; network disabled, source/model/corpus read-only, bounded CPU/memory/PIDs, local RTX 3080 Laptop GPU.
- Model Qwen2.5-0.5B-Instruct revision `7ae557604adf67be50417f59c2c2f167def9a775`; weight SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Corpus: 64 bundles × 16 suffixes, 270,228 bytes; SHA-256 `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.
- GPU-side construction had first retained a pre-model import STOP for packaging mismatch, then passed under freeze revision 2: all answer IDs, 1,024 token boundaries, cache isolation, and stale/foreign/changed-prefix rejection. See `CONSTRUCTION_ATTEMPTS.md` and the two construction records.

## Outcome

| Measure | Result |
|---|---:|
| Paired questions | 1,024 / 1,024 |
| Eight-code winner equality | 1,024 / 1,024 |
| Winner divergences | 0 |
| Full/cache winner ID 15 | 992 each |
| Full/cache winner ID 19 | 32 each |
| Independent recomputations | 1,024 pairs |
| Maximum independent-vs-stored vector absolute difference | 0.0 |
| Independent audit errors | 0 |

The vector-difference value above compares each retained vector with an independent recomputation of that same execution arm. It is **not** a full-prefill-vs-cache score-equality claim. Scores and top-two margins are retained in the raw rows; this issue's gate is winner equality only.

## Evidence hashes

- `formal01/ROWS.jsonl`: `a1e916e72901826be62f0fbe29656560a48c4fc0034672bcb382f7b27a9b92ee`
- `formal01/PROGRESS.jsonl`: `25c2879aaf89d97e651bb7f34887574c42bacc9d646f540afa09f1e0444c781d`
- `formal01/RUN.json`: `83978c9fb56cf82f27fdb8ca3b2ad07576ba3d583ab3e8342b34b2f128703a76`
- `formal01.SUPERVISOR.json`: `caf85a5ab3e1f5de150980119c0bdb0b2eb05f0637d33c405e49948a6149f037`
- `audit01/AUDIT.json`: `8b55b6a1b502b6c3bfffbbb9388e1c1f11cca1356be4abdb5c57f0e17a7e1712`
- Construction PASS: `527f70af7b311c6b4d6a057ae3e0028aa93bd3f0350589d56fe7a30a251f0cae`

## Scope / disposition

Keep the shared reader and all predecessor records unchanged. #4623's full-vocabulary STOP and #4639's selected-score tolerance STOP remain in force. This pass shows only that, on this one synthetic corpus/model/image/GPU, those score differences did not change any of the 1,024 eight-way winners. No training or fine-tuning was performed or needed for this inference-mechanics hypothesis.
