# A16 protocol

## Question
Does increasing model scale within the same Qwen3 family and quantization improve transition faithfulness under A15's frozen typed-conflict prompt, enough to permit a scoped schedule-sensitivity comparison?

## Allocation
- ID: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A16-MODEL-SCALE-20261008`.
- Fresh seeds 5601, 5602, 5603; four arms; six checkpoints; five held-out queries.
- 360 query calls plus 30 consolidation calls = 390.
- Model: `qwen3:14b`, 14.8B parameters, Q4_K_M; frozen digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- Dedicated private store `/tmp/unjuno-8406-t1-a16-ollama-store`, server on `127.0.0.1:11435`.

## Single intervention and controls
Relative to A15, only the model scale changes (Qwen3 8B to Qwen3 14B). Both are Q4_K_M variants. Prompt, JSON Schema, corpus/order, queries, schedules, decoding, auditor, and call budget are held fixed. Fresh seeds avoid pooling. No GUI, user data, action authority, or external effect is involved.

## Execution and interpretation
1. Freeze and preregister the package before inference.
2. Check private tag and every manifest layer; save preflight output and checksum.
3. Run the candidate once. No retry, seed replacement, or pooling.
4. If all 390 rows complete, run the independent auditor once.
5. Save raw/audit artifacts and checksums, then stop the private server.

An identity mismatch before generation is STOP with zero calls. Any call error, interruption, identity change, or incomplete row count is STOP/INCOMPLETE without retry. Any audit error or non-PASS_METHOD status is FAIL_METHOD, and answer/schedule contrasts remain descriptive only. A clean PASS_METHOD would permit scoped comparisons only for this fixture, model family, and seeds, not a product or GUI effectiveness claim.
