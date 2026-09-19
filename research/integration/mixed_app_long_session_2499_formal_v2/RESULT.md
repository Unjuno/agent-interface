# Formal allocation result: #2499 successor v2

This is a fresh additive allocation. It does not modify the retained STOP in
#2658 or any component result.

## H/T/D/C/U

- **H**: one persistent private X11 session can traverse the four declared
  mixed-app transitions while refusing stale admissions and preserving fresh
  identity.
- **T**: run `formal_session.py` once in the pinned local Docker image with
  `--network none`, using the repaired launch arguments and one Xvfb display.
- **D**: retain the emitted ordered ledger, process/window identities,
  geometry receipts, admission dispositions, input/model/network counters,
  and cleanup result.
- **C**: PASS only if all checks pass, including geometry change and distinct
  window replacement identity. Any failed check is FAIL; infrastructure setup
  failure before the allocation is STOP.
- **U**: whether the existing mixed-app image can provide stable geometry,
  focus, and non-reused replacement identity remains unknown.

## Local Docker result

Image: `mixed-app-2666:local`; network: none; display: `:142`; model calls: 0;
network calls: 0; input operations: 3; event count: 15.

Decision: `FAIL_MIXED_APP_LONG_SESSION`.

Observed failures:

1. Inkscape and Calc were enumerated, but both reported `Geometry: 1x1`;
   the geometry transition therefore did not change the recorded geometry.
2. After the focus-drift activation, `getactivewindow` returned `null`, so the
   focus check failed rather than being inferred as successful.
3. Chromium replacement returned the same window ID (`4194307`) as the old
   identity, so the required distinct replacement identity failed.

The session emitted a complete 15-event ledger and neutral cleanup record, but
the acceptance gate is not met. No integrated-session PASS is claimed.
