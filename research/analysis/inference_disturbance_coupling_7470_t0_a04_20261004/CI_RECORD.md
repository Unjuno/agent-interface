# Local checks — Issue #7470 A04

- Construction suite: 3/3 PASS before formal registration.
- Python byte-compilation and CRLF-aware diff checks: PASS.
- Frozen input hashes verified; output path absent at launch.
- Candidate invoked once, exit 0: four shifts / eight trajectories / eight events per trajectory.
- Independent auditor invoked once after candidate exit 0, exit 0; raw reconstruction exact; 3/3 mutations rejected; one seam event verified per trajectory.
- Analytical/workspace index and post-commit tree checks: pending final integration.
- Full product CI and hosted Actions: not run; finite stdlib method experiment only.
- Formal gate review found `centered_pearson_r` is normalized by an extra factor of period length in candidate and auditor; preregistered Pearson statistic is therefore wrong. A04 is not an Issue-level PASS; see REPORT.md. Formal pair was not rerun.
