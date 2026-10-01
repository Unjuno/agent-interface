# T7 local validation

- Containerized candidate, independent audit, and four corruption controls — PASS.
- Python syntax compilation in the container — PASS.
- Containerized `py_compile` — PASS.
- `python3 research/analysis/check_index.py --write` then `python3 research/analysis/check_index.py` — PASS; 212 retained result directories indexed.
- `python3 .github/check_public_navigation.py` — PASS after staging the new tracked path (26 documents, 913 repository-relative links).
- `python3 research/check_workspace_index.py` — cannot pass in this sparse worktree because numerous indexed top-level research directories are omitted. No indexes were changed to mask this checkout limitation; the hosted full-checkout workflow is required for this gate.
- No runtime or GUI tests are applicable to this exact enumerator.
