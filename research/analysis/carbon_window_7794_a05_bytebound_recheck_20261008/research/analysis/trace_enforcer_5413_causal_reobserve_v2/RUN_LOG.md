# Run receipt — `trace-causal-reobserve-5413-20261001-02`

Frozen source main: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`  
Environment: CPython 3.11.9, Windows host CPU, standard library only.  
Docker/GPU/CUDA/model/GUI/network calls: 0. Retries: 0.

## Exact commands and outcomes

1. `py -3.11 -B -m unittest discover -s research\issue-5413-causal-reobserve-v2 -p test_candidate.py -v` — exit 0; 8/8 passed.
2. `py -3.11 -B research\issue-5413-causal-reobserve-v2\run_candidate.py` — exit 0; stdout: `{"allocation": "trace-causal-reobserve-5413-20261001-02", "max_trace_length": 6, "raw": "raw.jsonl.gz", "trace_count": 137257}`.
3. `py -3.11 -B research\issue-5413-causal-reobserve-v2\audit_raw.py research\issue-5413-causal-reobserve-v2\raw.jsonl.gz` — exit 0; stdout: `{"errors": [], "missed_mutations": [], "mutation_controls": {"rejected": 5, "results": {"accept_stale_action": true, "accept_superseded_response": true, "change_trace": true, "clear_on_unlinked": true, "duplicate_pending_request": true}, "total": 5}, "passed": true, "rows_audited": 137257}`.

All six frozen source hashes were rechecked after execution and matched. The gzip JSONL raw contains exactly 137,257 ordered traces (length 0–6); gzip size 1,124,199 bytes, SHA-256 `4161f7cae2d8a5d4d07b40cac185c031c5552464e24457ecc9436cfcfe382d1e`. Decompressed UTF-8 payload size 77,327,886 bytes, SHA-256 `d58259ada5635fdda3979a4aa66859a11456be68145a57af8fceffbc027e9e9b`. It includes the superseded-response/action counterexample-length sequence. Counts are finite synthetic traces, not runtime effects.
