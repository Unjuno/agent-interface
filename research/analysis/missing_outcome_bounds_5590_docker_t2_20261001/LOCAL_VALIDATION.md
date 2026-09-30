# T2 local development validation (not formal container evidence)

## Result

The byte-frozen candidate and ledger were executed on the local macOS host. The independent auditor was then run separately against the persisted raw JSON. It returned `PASS_BOUNDS_SCOPED`, errors empty, `N=10, S=6, F=1, M=3`, exact interval `[3/5, 9/10]`, and all 8 compatible completions. Raw and audit bytes and SHA-256 values are retained in `results/local-development-01/`.

Construction tests passed 8/8. Five integrity mutations were independently rejected: dropped unresolved denominator row, unresolved-to-failure relabel, duplicate episode identity, boolean threshold numerator, and duplicate completion mask. Python byte-compilation, analysis-index, workspace-index (`--git-tree`), public-navigation, YAML parse/structural checks, and `git diff --check` passed.

## Container boundary

No local Docker container ran in this development validation. `orbctl status` reported OrbStack `Running`, but its Docker socket dated 2026-09-26 did not answer `docker info` within 8 seconds, using both the configured context and OrbStack's bundled Docker CLI. `orbctl doctor` also reported that the active Docker CLI resolves to a Nix installation rather than OrbStack. No daemon restart or other host-service mutation was performed. This is an environment limitation, not a scientific result and not the formal T2 allocation outcome.

The formal T2 workflow remains a fresh one-shot Docker allocation: the output-mount write/read/delete probe runs first with the numeric Actions runner UID:GID; only a passing probe and construction suite permit the candidate, and only a persisted candidate output permits the independent raw-only auditor. The formal container result must be reported separately from this host-only PASS.

## Reproduction

From this directory:

```sh
python3 -B -m unittest -v test_bounds.py
python3 -B candidate.py ledger.json /tmp/5590-t2-local-raw.json
python3 -B audit.py ledger.json /tmp/5590-t2-local-raw.json
```

The raw result is a deterministic synthetic finite cohort only; it does not establish a real cohort's promotion status, population effect, or task utility.
