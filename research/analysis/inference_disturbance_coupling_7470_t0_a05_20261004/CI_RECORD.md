# Local checks — Issue #7470 A05

- Construction suite: 3/3 PASS before formal registration.
- Python byte-compilation and whitespace check: PASS.
- Frozen hashes verified and formal output absent at launch.
- Candidate invoked once (exit 0): four shifts, eight trajectories, eight events each.
- Independent auditor invoked once after candidate exit 0 (exit 0); exact raw reconstruction; Pearson fixture exact; seam rows 8/8; mutations 3/3 rejected.
- Analytical index tests: 17/17 PASS; workspace-index test: 1/1 PASS; Git-tree workspace index: 159 top-level directories reachable.
- Post-integration Python byte-compilation and `git diff --check`: PASS.
- Full product CI and hosted Actions: not run; bounded standard-library method experiment only.
