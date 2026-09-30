# Local validation

Executed in the sparse worktree based on `5a741e5fe4d427a560c21975b8a0b693fb48fd66`:

- `python research/analysis/check_index.py --write` — refreshed generated result index to 206 retained directories.
- `python research/analysis/check_index.py` — PASS, all 206 indexed.
- `python .github/check_public_navigation.py` — PASS, 26 documents / 902 repository-relative links. The first pre-staging invocation could not resolve the newly added report because it was not yet tracked; after staging the additive files it passed.
- `python -m py_compile .../experiment.py .../audit.py .../audit_v2.py` — PASS.
- `git diff --cached --check` — PASS after removing trailing blank-line warnings.
- `python research/check_workspace_index.py` — local sparse-checkout limitation: reports numerous existing top-level research directories as absent because this worktree hydrates only selected folders. No root research namespace/index change was made to mask this. The matching full-checkout hosted Research Workspace Index workflow must pass before merge.

Formal simulator and both raw-audit executions are recorded separately in [EXECUTION.md](EXECUTION.md); this local CI section is not a substitute for them. Hosted CI on the final PR head remains required before integration.
