# Construction boundary run 01 — HOLD

This report preserves one local Docker zero-update construction-boundary test invocation for Issue #4929. It is not a role-network or online-LoRA quality result.

- Image: needle-pilot05:local, ID sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e, linux/amd64, Python 3.12.14.
- Docker: 29.8.0, daemon linux/x86_64; --pull=never --network none --read-only --cpus=0.25 --memory=2g --pids-limit=64; source mount read-only.
- Result: 12 tests, 9 pass, 3 fail, exit 1, 0 optimizer steps, 0 construction-seed runs, 0 formal fits, 0 retries.
- Disposition: HOLD_SOURCE_FREEZE_MISMATCH. At launch, source GitHub blob IDs for launcher/test files had advanced beyond those captured in the pre-run FREEZE. Exact GitHub identities and mounted-file SHA-256 values are retained in RUN_SOURCE_MANIFEST.json. Therefore the run is not eligible for construction PASS even aside from the three failing test fixtures.
- Observed failures are fixture/expectation setup defects: required fresh directories/source fixture were absent, causing earlier fail-closed checks to win. The output did not establish that log/output separation passes or fails under valid host bindings.
- The predecessor #4911 STOP and original #4929 FREEZE are unmodified. No rerun is authorized under this allocation. Formal seeds 9934211, 9934311, and 9934411 remain unspent. No hypothesis conclusion is claimed.