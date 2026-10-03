# A03 construction history (not formal evidence)

Before freezing A03, a local macOS/Python 3.14 construction pair was run on
the deterministic fixtures and code. The first candidate output was generated
once and retained at `construction_a03_preflight_20261003/candidate.raw.json`.
The first audit returned nonzero with 24 false mismatches because its replay
loop accidentally used the final fixture's vote count and dimensions when
checking prior rows; that exact first `audit.json` is retained at
`construction_a03_failed_audit_20261003/audit.json`.

The independent auditor was corrected to store per-row replay counts and pixel
visits during reconstruction. The candidate output was not changed or rerun.
The corrected construction auditor returned exit 0: 20/20 rows replayed,
errors 0, all four injected corruptions rejected for the intended reason, and
all ten exact 1x/2x fixture pairs invariant. Metrics were persistence 14/14
determinate, 0 false-confident; pixel template 8/14, 10; single threshold
14/14, 6. These are construction checks only and are excluded from A03 formal
allocation counts and claims. The frozen OrbStack A03 candidate and auditor
will each run once against fresh output storage.
