# Local validation

Run in the sparse worktree based on `1e34cef0b9c9b729aa0fbd32785dd658a4b6c94f`:

- `python research/analysis/check_index.py --write` — refreshed generated result index to 210 retained directories.
- `python research/analysis/check_index.py` — PASS, 210 indexed.
- `python .github/check_public_navigation.py` — PASS, 26 documents / 911 repository-relative links.
- `python -m py_compile .../experiment.py .../audit.py` — PASS.
- `git diff --cached --check` — PASS.
- `python research/check_workspace_index.py` — cannot pass locally because this checkout is sparse and omits many existing top-level research directories; no root-index workaround was made. Require the full-checkout hosted Research Workspace Index workflow before merge.

The one-shot pinned-container experiment and independent raw audit are recorded in [EXECUTION.md](EXECUTION.md); they are separate from these documentation/index checks. Hosted CI for the final PR head remains required.
