# Issue #3266 — isolated-display Chromium generation audit

This is an additive successor to #3212. It does not reinterpret or replace
the retained graceful/forced-restart STOP records.

The live runner must emit one JSON object per allocation to `RAW.jsonl`, plus
`MANIFEST.json`, stdout/stderr, and source/image digests. The audit is
fail-closed: a new CDP target or a new X11 window is not sufficient by itself;
the admitted generation must correlate CDP browser/process identity, X11
`_NET_WM_PID`, display, profile, and launch epoch before input is dispatched.

Required controls are `stale_xid`, `old_process`, and `positive_p2_effect`.
Only the positive control may dispatch input, and it must report an
independent DOM effect. A diagnostic STOP is a valid outcome; it is never a
PASS or a live-effect claim.

Run in a pinned container with `--network none`. The formal workflow is not
included until the live runner and fixture are reviewed.
