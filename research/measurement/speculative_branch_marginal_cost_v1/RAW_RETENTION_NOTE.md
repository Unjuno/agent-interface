# Raw timing retention note

The formal invocation produced `RAW_TIMINGS.json.gz` containing all 100,000 paired K1/K2 iteration timings and derived marginal values. Frozen identities:

- raw JSON: 1,910,660 bytes, SHA-256 `412af339d3145f7b0b8b4b9475e5735fd4070314a97f18e25d91517d4418bb3b`;
- gzip artifact: 725,602 bytes, SHA-256 `b8bbe82be1579d05db6a3b4d199bbea7b59dc2e4318a3181ef46f15ffae9e9cf`;
- lossless uint64 packing: 1,600,014 bytes, SHA-256 `673a36223044605441e993836e16047ef2a3f423fb5cf7c10fe32987c1688364`;
- XZ of the packing: 360,956 bytes, SHA-256 `436993d758810eeb1bd74c54de672d26cd8e94493d9ac65aa9b5aa8f72b39af5`.

The frozen auditor consumed the full raw vector and recomputed all K1/K2/marginal summaries. A copied raw-vector mutation was rejected for paired-difference, summary and hash mismatch.

The current ChatGPT GitHub connector is text-oriented; publishing the ~0.48 MB Base64 representation would add a large transport-only payload. This branch therefore retains the exact raw commitments plus the audited summaries, source freeze, packing manifest/reconstructor and corruption results. This publication limitation does not alter or rerun the formal result.
