# Run receipt — `trace-causal-reobserve-5413-20261001-01`

Frozen source main: `2197bead5ffa7dc226390becc811913159c8438e`  
Environment: CPython 3.11.9, Windows host CPU, standard library only.  
Container/GPU/CUDA/model/GUI/network calls: 0.  
Retries: 0.

## Exact invocations and outcomes

1. `py -3.11 -B -m unittest discover -s research\issue-5413-causal-reobserve-v1 -p test_candidate.py -v` — exit 0; 8 tests passed, 0 failed.
2. `py -3.11 -B research\issue-5413-causal-reobserve-v1\run_candidate.py` — exit 0; stdout: `{"output": "raw.json", "trace_count": 2801}`.
3. `py -3.11 -B research\issue-5413-causal-reobserve-v1\audit_raw.py research\issue-5413-causal-reobserve-v1\raw.json` — exit 0; stdout: `{"errors": [], "missed_mutations": [], "mutation_controls": {"rejected": 5, "results": {"accept_stale_action": true, "change_trace_event": true, "clear_on_unlinked": true, "drop_trace": true, "duplicate_pending_request": true}, "total": 5}, "passed": true}`.

The independent read-only receipt check confirmed all six frozen source SHA-256 values match. The retained raw JSON payload is 1,205,232 bytes, SHA-256 `ce5f73d03c2ed017328060d633ac6a7473f9c96ef8fd037419f8c3c6e07b153d`; GitHub stores those exact UTF-8 bytes in `raw.json.gz` using gzip transport compression. It contains 2,801 traces, 1,534 action events (1,247 admitted and 287 rejected), and 262 reobserve requests. Counts describe the exhaustive synthetic trace set only.
