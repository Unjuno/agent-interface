# Capture timing boundaries

Optional X11 PNG artifacts include `timing_ns`, measured using the local monotonic clock:

- `started` to `converted`: raw X11 pixel conversion to RGB.
- `converted` to `encoded`: PNG encoding and retrieval of encoded bytes.
- `encoded` to `written`: unique path creation, exclusive file open, write and close. No fsync guarantee.
- `written` to `hashed`: encoded and raw SHA256 computation.

These timestamps start after format/length validation. The existing backend `capture_started_ns` and `capture_ended_ns` still bracket only GetImage. Intervals must not be presented as complete observation latency or summed with enclosing intervals.

The research NativeHandleBridge additionally records `started`, `public_returned`, `binding_checked`, `artifact_verified` and `decoded`. The public-return interval includes initial binding checks and the shared observation call. The binding-checked interval includes report persistence and the subsequent binding check. Verification includes reading the artifact and checking its hashes. The decoded endpoint precedes history/publication writes and transport to a model. It is not first useful feedback or semantic completion.

No capture is removed, no image compression setting is changed, and timing adds no input authority. Failed artifact preparation keeps the existing artifact_error behavior; partial artifact timing is not emitted. Bridge failures keep their existing error path.

Local validation: six artifact tests passed, plus shared native protocol/harness checks (results-local/capture-stage-timing-check-01). Three separate Xvfb setup attempts produced no capture. The third retained stderr shows Unix listener creation failure; earlier attempts retained timeout notes only. Results remain in capture-stage-timing-live-01 through -03. A fourth attempt used the existing PrivateSession path and correctly rejected a binding change during capture. A fifth, separately allocated static fixture waited for ten consistent binding samples and completed five public observations with ordered timestamps. See runtime/results/capture-stage-timing-01. These construction captures verify instrumentation, not task latency, speedup or model delivery. Earlier failures remain retained.
