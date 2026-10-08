# Issue #8618 — A01 pre-candidate infrastructure STOP

Allocation `8618-T0-A01-20261009` was frozen at commit `aed089bab5eba50e3c596e345bac5030630f4329`, based on main `3dc1f09a8bb3bd5498bba2936f5965ce3024b2ce`. Its formal runner exited 1 while checking frozen file hashes because it resolved package-relative paths from the repository root. The failure occurred before the execution lock and before the candidate subprocess.

Candidate invocations: 0. Auditor invocations: 0. No scientific result exists for A01. The exact failure and preserved state are in [PRE_CANDIDATE_STOP.json](raw/PRE_CANDIDATE_STOP.json). A01 was not retried. The corrected runner was frozen under the separate A02 allocation and output path.
