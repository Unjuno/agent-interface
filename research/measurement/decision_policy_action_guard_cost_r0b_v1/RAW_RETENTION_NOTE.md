# Raw timing retention boundary

The one formal invocation produced `FORMAL_RESULT.json` with all 60,000 in-process timings, 60,000 AF_UNIX timings and 10,000 invalidation-to-refusal timings. The frozen `audit.py` consumed those raw vectors directly and recomputed every retained summary.

Exact commitments:
- raw JSON: 717,719 bytes, SHA-256 `cec1844635f6f26d6271e66922c45b2208f36f24373cadf6ce06c6a754935d3f`;
- deterministic gzip: 200,518 bytes, SHA-256 `7a676445060d39fae3c10cd62cc928d871b95bb6e0703dcaf6f6bf0e810704ce`.

The current ChatGPT GitHub connector is text-oriented. Duplicating the gzip as Base64 would add about267k transport characters without changing the scientific evidence. The repository therefore retains the exact commitments, audited summaries, source freeze, postformal rehash and corruption evidence. `reconstruct_result.py` verifies a separately retained raw or gzip artifact against these commitments; it does not synthesize missing data.

This is a publication-transport boundary only. The formal invocation was not rerun and no timing row was replaced by a summary during the audit.
