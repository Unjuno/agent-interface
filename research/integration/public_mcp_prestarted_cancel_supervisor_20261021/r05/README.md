# R05 — keep archive bookkeeping out of public call records

## Result

After terminal cancellation payloads moved to `cancellation.json`, the archive
marker and operation ID still appeared in the public `call` or `retained_call`
record. R05 removes those implementation fields from the response while
preserving the public `cancellation` subrecord and its operation identity.

The four focused suites passed **106/106 tests in normal Python** and
**106/106 under `-O`**. Normal runtime was 42.602 s; optimized runtime was
43.230 s. Raw stdout/stderr, exit codes, conditions and source fingerprints are
retained here.

## Limits

This remains Windows/Python with deterministic Fake X. It does not exercise the
production X11 worker against Xlib or Xvfb, prove late queued-effect exclusion,
or qualify blocked-live-server release, independent task success, recovery,
MAP01, physical input, efficiency or reliability. No WSLc or Docker allocation
was used.
