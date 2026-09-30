# Local validation

Final local checks were rerun in the sparse worktree after rebasing the evidence branch onto `9abdfdc48d61c3d25d538a3acb1444d774a905d1`. The formal source files and raw bytes match their pre-run hashes/blob identities in [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md).

- `python research/analysis/check_index.py --write` — refreshed generated result index after adding the report.
- `python research/analysis/check_index.py` — PASS, all 209 retained directories indexed at the final base.
- `python .github/check_public_navigation.py` — PASS, 26 documents / 908 repository-relative links at the final base. The first pre-staging invocation could not resolve the newly added report because it was not yet tracked; after staging the additive files it passed.
- `python -m py_compile .../experiment.py .../audit.py .../audit_v2.py` — PASS.
- `git diff --cached --check` — PASS after removing trailing blank-line warnings.
- `python research/check_workspace_index.py` — local sparse-checkout limitation: reports numerous existing top-level research directories as absent because this worktree hydrates only selected folders. No root research namespace/index change was made to mask this. The matching full-checkout hosted Research Workspace Index workflow must pass before merge.

Formal simulator and both raw-audit executions are recorded separately in [EXECUTION.md](EXECUTION.md); this local CI section is not a substitute for them. Hosted CI on the final PR head remains required before integration.
