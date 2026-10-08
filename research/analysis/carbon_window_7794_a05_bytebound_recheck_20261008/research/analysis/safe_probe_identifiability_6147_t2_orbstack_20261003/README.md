# Issue #6147 T2 lifecycle successor

This new allocation follows T1's preserved `STOP / NOT_EVALUATED`; it is not a retry. T1 stopped because the finite fixture closed Xvfb before `PixelController.close()` finished flushing. T2 catches only `Xlib.error.ConnectionClosedError` from final `Display.close()` and adds regression tests proving unrelated close errors still propagate.

H/T/D/C/U and no-retry rules are in [PROTOCOL.md](PROTOCOL.md); prelaunch counts and immutable identities are in [FREEZE.json](FREEZE.json). Copied policy, model, fixture, auditor, candidate, and matched inputs are bound by [SHA256SUMS.txt](SHA256SUMS.txt). The teardown ordering reproduced successfully in a construction-only adaptive run; details and the earlier host-Xlib test discovery failure are preserved in [CONSTRUCTION_STOPS.md](construction_smoke/CONSTRUCTION_STOPS.md), with construction raw checksums in `construction_smoke/lifecycle_run_01/SHA256SUMS.txt`. Construction activity is not formal evidence.

The formal run completed as `H_PASS_SCOPED`; see [REPORT.md](REPORT.md), [RUN_RECORD.json](RUN_RECORD.json), and the [immutable raw manifest](raw/formal_02/SHA256SUMS.txt). The runner used separate `raw/formal_02/` and unique container names, invoked each of adaptive/no_probe/one_step once, then ran the independent raw-only auditor once. The T1 record and raw remain unmodified.
