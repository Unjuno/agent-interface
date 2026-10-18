# MAP01 V39 Xvfb per-key release identity A05

A05 tests the exact current-main V39 release-batch backend and owner v4→v3→v12 against one isolated Xvfb client. A03 and A04 stopped on harness defects; their raw outcomes remain untouched. Only the immediate typed backend parent is shimmed.

Read `PREREGISTRATION.md` and verify `FREEZE.json` and `SHA256SUMS` before the one candidate invocation. The candidate runs once; any incomplete trace is `STOP`, never a retry.

This synthetic test does not run Doom or use a desktop app, physical input, network service, model, or Issue #59 private lane.
