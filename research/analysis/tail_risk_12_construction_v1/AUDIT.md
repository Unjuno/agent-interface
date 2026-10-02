# Raw-only arithmetic audit

`audit_raw.py` reads only the retained `result.json`; it does not import or run `check.py`. It independently recomputes the worst-10 mean for identical positive losses via `min(failures, 10) × severity / 10`, checks all 5,151 ordered binary failure-count pairs, and rejects five in-memory corruptions of the retained result (binary tail, severity tail, pair count, scope, boolean type).

Host command used:
`docker run --rm --network none --read-only --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work,target=/work,readonly python:3.12-slim python -B /work/issue12_tail_audit_raw.py`

Exit 0, stdout:
```json
{
  "audit": "RAW_ONLY_ARITHMETIC_PASS",
  "candidate_imported": false,
  "binary_pairs_independently_checked": 5151,
  "corruption_controls_rejected": 5,
  "empirical_result": "UNTESTED"
}
```

The local filename/sidecar `issue12_tail_result.json` correspond to published `audit_raw.py`/`result.json`; the script supports both names. This is an independent calculation and retention check of *authored losses*, not an independent measurement or validation of severity=10 for any GUI event. The empirical #12 hypothesis remains untested; forbidden-effect hard gates remain separate.
