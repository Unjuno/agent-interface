# Construction record

- Base main: `52c42c40bb074f46db1dc74afb20508e68bc1282`.
- Branch: `research/6645-coverage-gate-counterfactual-t1b-20261003`; dedicated
  worktree created from latest main. No colliding open PR/branch found in the
  bounded #6645 coverage-gate search.
- The corrected candidate input uses a separate `candidate_input/` mount;
  oracle labels are stored outside it and are only mounted into the independent
  auditor container. Candidate and auditor source files are distinct.
- Runtime: OrbStack Docker Engine 29.4.0, CLI 29.5.2. Pinned cached image is
  Python 3.12.14, Linux/arm64, digest
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Construction suite passed 5/5; source compilation and runner shell syntax
  passed. Formal candidate/auditor invocations before freeze: 0/0.
- The T1 erratum was posted to Issue #6645 as comment #5960211409. T1 source,
  raw results, and merged record remain unchanged.

Memory/swap are requested Docker configuration, not a host/cgroup enforcement
claim.
