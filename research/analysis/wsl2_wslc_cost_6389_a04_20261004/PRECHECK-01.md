# Construction preflight 01 — incomplete runner receipt

This was a setup check only; no `runtime/integration_checks/native.py` suite
candidate or formal pair was started.

- WSLc 3.0.1.0, pinned A08 image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`.
- Command mounted the frozen checkout read-only at `/src` and a fresh output
  directory writable at `/out`, then attempted `git rev-parse HEAD`,
  `git status --porcelain`, dependency imports, and `/out` write verification.
- The visible stdout reached `HEAD=44d6eff4e204ccc318f2dc4f5181964bdf2c94bb`.
  No dependency line or output-volume marker appeared. WSLc emitted its known
  cgroup/swap warning.
- The `--rm` preflight container was later absent from the running-container
  inventory; no other container was touched. The host wrapper's terminal exit
  code/output tail was not retained, so this is explicitly an incomplete
  construction receipt, not a typed runtime STOP or a successful preflight.

The command included `git status` against a read-only source mount, which can
attempt index refresh/write-lock operations. The next setup check will use only
read-only Git object queries (`rev-parse`/`show`) plus source import and mount
checks. This correction does not repeat, retry, or count a formal candidate.
