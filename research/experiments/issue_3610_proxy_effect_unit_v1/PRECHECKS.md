# Issue #3610 construction and preflight record

The following checks are excluded from the 28-row formal allocation:

- Pinned container identity: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64.
- Container policy: `--network none --read-only`; source bind-mounted read-only; only `/tmp` supplied as tmpfs for Xvfb and temporary directories.
- Proxy image determinism/state-sensitivity test: 1/1 PASS.
- Python AST parse for every source module: PASS.
- GTK/Xvfb fixture construction smoke: PASS; actual XTest click acknowledged, title/counter changed from `proxy-fixture:0:1` to `proxy-fixture:1:2`, independent fixture log contains one effect event.

One earlier construction-only smoke reached the correct visible effect but exited with `ConnectionClosedError` because its cleanup closed the Xlib connection after terminating Xvfb. The exception and exact teardown cause were preserved. `preflight.py` was corrected to close the Xlib client before terminating Xvfb; the final smoke above passed. No 28-row formal runner invocation occurred during construction/preflight.
