# Frozen auditor v1 first outcome

Command: `python3 research/analysis/action_bound_relevance_6619_a01_20261005/audit.py research/analysis/action_bound_relevance_6619_a01_20261005/inputs/public_cases.json research/analysis/action_bound_relevance_6619_a01_20261005/inputs/scorer_oracle.json research/analysis/action_bound_relevance_6619_a01_20261005/results/candidate.raw.json`

Exit: 1. Start/end UTC: 2026-10-05T02:47:29Z / 2026-10-05T02:47:29Z. Stdout file `audit.json` is zero bytes. The stderr traceback ended at `audit.py:89` with `KeyError: 'sha256'`: frozen field is `source_sha256`. No case rows, metrics or corruption controls were evaluated.

This failed audit is retained. The candidate was not rerun. Versioned audit v2 is a separately labelled postrun reconstruction.
