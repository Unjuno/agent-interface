# Local checks — Issue #7470 T0

- Construction suite: 5/5 PASS before formal registration.
- Python byte-compilation of candidate, auditor and tests: PASS.
- CRLF-aware `git diff --check`: PASS.
- Post-formal rerun of the construction suite: 4/5 checks pass; the prelaunch-only `formal_output_is_absent_before_launch` check fails because the immutable formal `results/` now exists. Candidate/auditor were not rerun.
- Formal `results/` absent before launch.
- Formal candidate: once, exit 0; 24 pairings / 48 trajectories.
- Independent raw-only auditor: once after candidate exit 0; exit 0; 48/48 reconstructed; mutations 3/3 rejected.
- Applicable analytical-index tests: 17/17 PASS; research workspace-index test: 1/1 PASS; `check_workspace_index.py --git-tree`: 159 top-level directories reachable.
- After adding the index rows, Python byte-compilation and `git diff --check`: PASS.
- Host-only standard-library test; no container, model, GUI, network, GPU, or actuation.
- Full repository CI and hosted Actions: not run; this finite stdlib experiment does not require the full product suite.
