# Local CI — homology/homotopy T0 A01

| Gate | Result |
|---|---|
| Construction unit tests | PASS, 7/7, pinned container |
| Non-writing syntax compilation | PASS |
| Formal candidate | PASS, exit 0, one invocation |
| Independent raw-only auditor | PASS, exit 0, one invocation, zero errors |
| `git diff --cached --check` | PASS |
| `python research/check_workspace_index.py --git-tree` | PASS, 160 top-level research directories reachable |
| `python research/analysis/check_index.py` | Exit 0 in sparse mode; reported index stale because many sibling result directories are absent from this checkout. The new path is indexed; full-repository analysis-index gate remains GitHub CI. |
| GitHub Actions | Pending PR creation after local validation |
