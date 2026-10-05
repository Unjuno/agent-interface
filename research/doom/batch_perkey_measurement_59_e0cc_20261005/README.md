# Batch-compatible per-key measurement

Read `RESULT.md` for the change, executed checks, repaired counterexample and scope. `PLAN.md` is the pre-test H/T/D/C/U. Run folders preserve original result status, source maps and stdout/stderr, including all first failures. The retained older A01 fixture is read-only compatibility input.

`source-blobs/<sha256>.py.txt` are inert exact executed Python source versions referenced by the run source maps. No snapshot is imported or discovered as a test. Production/test changes are separate normal repository files. `production.patch` is the initial tracked production diff; `production-final.patch` includes the final eight production files and the audit-driven batch downgrade repair.

Public copies replace only private path prefixes/session identifier; `public-custody.json` maps original and published hashes. Receipt output hashes refer to original retained bytes; use this mapping when a normalized public log differs. `publication-manifest.json` verifies the published files. Source snapshots and the historical public fixture preserve exact bytes.

The tests use fake Xlib and real owner threads, plus a startup interception before Session. Full V39 controller, live X/game/model, latency, task effect and application consumption are unverified. The private runner uses paths relative to its private job export and is kept as inert reproducibility evidence; reconstitute the source tree from source maps before using it. No formal allocation was run or replayed.
