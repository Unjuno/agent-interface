# Architecture proposals and implementation status

This directory holds architecture proposals and design records. Each entry states whether the design is implemented, what evidence supports it, its qualification boundary, and the next discriminating check. A design document does not grant runtime or experiment resources.

## Prestarted cancellation supervisor

[`PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md`](PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md) records the opt-in owned `guarded-x11` supervisor design and its current evidence. The implementation and public-MCP composition are merged, but the path remains default-off. A retained standard-caller Xvfb run observed one release and independent key-up readback through an injected delayed-request horizon; the runtime receipt correctly remains `UNKNOWN`, `release_confirmed=false`, `task_success=null`, and replay denied while `late_server_request_possible=true`.

The next useful checks are fresh-target recovery and evidence-based resolution of the delayed-request/late-effect boundary. The design does not qualify general release safety, physical desktop control, MAP01, WSLc, integrated efficiency, or reliability. Keep Issues #17 and #57 open for their remaining questions; WSLc stays on HOLD under #7924.

The separate Win32 operation-owner candidate is a reviewable proposal in
[`../superpowers/specs/2026-10-22-win32-prestarted-supervisor-design.md`](../superpowers/specs/2026-10-22-win32-prestarted-supervisor-design.md).
It is not the X11 supervisor implementation and does not authorize native
input, runtime adoption, or a new allocation. Keep its process-generation,
input-authority, and release evidence distinct from the X11 record above.
