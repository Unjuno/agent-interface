# A01 execution record

Disposition: `FAIL_HARNESS` — preserve as the first formal run of frozen A01.

- Frozen source: `FREEZE.json`; no candidate/oracle/source edits after freeze.
- Exact source/image: hashes in `FREEZE.json`; Python image pinned by digest,
  `linux/arm64` on OrbStack/Docker.
- Command: `docker run --rm --network none --cpus=1 --memory=1g
  --pids-limit=64 --mount type=bind,src=<A01-dir>,dst=/t0,readonly -w /t0
  python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f
  python -B -m unittest -v test_model`
- Exit: 1; 7 tests ran, 6 passed, 1 failed in 0.002s (container wall time
  0.473s).
- Failure: `test_blind_inverse_loses_the_disjoint_external_write` asserted that the
  post-interleaving fixture still had body `x`. The trace correctly has body
  `y`; the blind policy output then restores `x`, while field-scoped output
  retains `y`. The erroneous assertion inspected the input fixture, not the
  blind policy result.
- The separate 28-row candidate/oracle reconstruction, all five fail-closed
  history tests, selectivity check, and two oracle mutation-detection checks
  passed in this run. A01 is not a PASS because its full frozen gate failed.
- No container image was pulled or changed; the workspace files were mounted
  read-only. No retry or source repair is attributed to A01.

Next: preserve A01 and create a separately numbered A02 freeze that changes
only the erroneous test assertion, reruns the full validation once, and records
its own source hashes/result. A02 would not rewrite or supersede this A01 raw
failure.
