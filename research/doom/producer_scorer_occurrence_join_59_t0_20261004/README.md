# Acknowledged producer → scorer → key occurrence join (Issue #59)

This deterministic construction tests the composition seam that remained after
the acknowledged scorer candidate (#7545), temporal attribution (#7537/#7544),
and owner-scoped occurrence reducer (#7546) were built separately.

The candidate drives the frozen `AcknowledgedSampler` with a fake game, sends
the resulting samples through the current-main `ProgressClock`, links a
positive progress event to its exact acknowledged sample, and then passes that
event through the frozen occurrence-aware release reducer. The resulting
`unique_temporal_occurrence` is limited to a same-run temporal association; the
output explicitly does not claim causation or game/application consumption.

The H/T/D/C/U question and source freeze are in `FREEZE.json`. The Linux raw and
a CRLF reconstruction of the Windows serialization are retained separately
because Windows text mode writes CRLF while Linux writes LF. The original
Windows raw path was overwritten by the planned WSL replay; the reconstruction
matches the SHA-256 captured in `RUN_WINDOWS.json`. Their canonical JSON content hash is
`af6d6ced5341f421a42685f9fd9e47e25b504b89257696c200fddd5f77772591`. A
cross-platform audit confirms parsed JSON equality, and the 25-file SHA-256
manifest verifies with `MANIFEST_AUDIT.json`.

## Result

Ten focused tests pass on Windows Python 3.13 and Ubuntu WSL Python 3.12. The
independent audit returns `PASS_SCOPED_SYNTHETIC_SOURCE_COMPOSITION`: the
positive event joins to producer run `run-A`, sample 2, update 2, then to the
unique owner occurrence `owner-a:1`. The cross-run mutation is rejected, and an
event exactly at the release/XSync start remains `unresolved_release_boundary`.
The explicit key-up receipt and cancellation-batch release interval both
preserve the occurrence through the reducer.

The first auditor version is preserved as `audit.py` with its failure noted in
`AUDIT_v1_failed.txt`. It moved only the event timestamp, so the join correctly
refused the event before the intended release-boundary assertion. `audit_v2.py`
changes the matching sample timestamp as well. The raw candidate content was
not edited to repair the audit; the deterministic runner later emitted the
same canonical JSON data from WSL, with its native LF line endings.

## Limit

This does not yet show actual source/runtime wiring. In particular, the
occurrence candidate's current admission and release records do not carry the
scorer's run ID. This join therefore requires a run ID on each owner-side row
and tests that requirement using synthetic telemetry. Without that field it
fails closed. The next runtime integration must propagate the scorer run
identity into actual owner admission and release telemetry before the joined
reducer can operate on a controlled session.

No ViZDoom engine, V16 session, X11 server, model, GPU, game allocation,
physical input, task effect, or recovery test ran. `wslc.exe` is unavailable on
this Windows host; the deterministic CPU construction ran in native Windows
Python and the installed Ubuntu WSL distro. This is not a freshness, latency,
causal-effect, release-time, gameplay, or live-control qualification.
