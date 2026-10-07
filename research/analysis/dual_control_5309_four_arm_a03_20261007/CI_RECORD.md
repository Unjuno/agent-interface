# A03 local verification record

Pre-freeze construction checks on final frozen sources:

- `python3 -m unittest -v test_construction.py` — 17 passed.
- `python3 -m pytest -q test_construction.py` — 17 passed.
- `python3 -m py_compile candidate.py auditor.py contracts_snapshot.py test_construction.py` — exit 0.
- `python3 research/check_workspace_index.py --git-tree` — 160 top-level research directories reachable.
- `git diff --check` — exit 0.
- Pinned `runtime/kernel/contracts.py` source snapshot SHA-256 matched the source at frozen main.

The local checkout is sparse. The full retained-analysis index cannot be certified from its absent sibling directories; do not run `research/analysis/check_index.py --write` here. The GitHub `analysis-index` workflow is the authoritative complete-tree gate. No candidate/auditor formal invocation was repeated for these checks.
