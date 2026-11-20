# V39/V15 post-batch keymap sampling A05

## H / T / D / C / U (fixed to the Issue #59 preregistration)

- **H:** A read-only X11 `query_keymap` sample immediately after the actual owner `input_state` sample and before per-key release-row publication can detect a missed fake-server release without inserting queries between explicit key-up injections. Missing/malformed query evidence must produce UNKNOWN.
- **T:** On frozen current main, use exact V39 selector/V15 backend source, real release-batch backend, owner-v4/v3 and runtime owner-v12 with an inert FakeX display. One candidate invocation runs three separate fresh-display cases: normal two-key release; one deliberately dropped fake-server key-up injection; post-batch query unavailable. Capture every down/up/XSync/query/input_state/emit ordering and emitted rows. One raw-only independent audit.
- **D:** PASS_METHOD_SCOPED only if normal rows report both keys absent at post-batch sample; the dropped-injection case identifies the still-down key and downgrades its row while retaining the other key's result; unavailable/malformed sample reports UNKNOWN; no keymap query occurs between UP injections; no physical/application authority is claimed.
- **C:** Fake-server call seam only. Actual production V15 telemetry backend, owner-v4/v3 and runtime owner-v12 source execute. Sampling wrapper is placed after returned `input_state` and before the backend emits release rows. Fake XTest can deliberately omit one server-state mutation while returning from the injection call.
- **U:** This is synthetic server bitmap evidence, not hardware state. No full V39 startup, live X11/OS input, application consumption/effect, latency bound, feedback quality, recovery, threat control, MAP01, or live allocation.

The preregistered experiment is a distinct A05 successor to release-order A04. It does not rerun PR #7887's nested classifier experiment or the prior startup-order A01 candidate.
