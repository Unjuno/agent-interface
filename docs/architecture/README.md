# Architecture proposals and implementation status

This directory holds architecture proposals and design records. Each entry states whether the design is implemented, what evidence supports it, its qualification boundary, and the next discriminating check. A design document does not grant runtime or experiment resources.

## Prestarted cancellation supervisor

[`PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md`](PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md) records the opt-in owned `guarded-x11` supervisor design and its current evidence. The implementation and public-MCP composition are merged, but the path remains default-off. A retained standard-caller Xvfb run observed one release and independent key-up readback through an injected delayed-request horizon; the runtime receipt correctly remains `UNKNOWN`, `release_confirmed=false`, `task_success=null`, and replay denied while `late_server_request_possible=true`.

The next useful checks are fresh-target recovery and evidence-based resolution of the delayed-request/late-effect boundary. The design does not qualify general release safety, physical desktop control, MAP01, WSLc, integrated efficiency, or reliability. The 2026-11-10 GitHub snapshot reports #17 closed/completed despite retrieved comments saying to keep it open; reconcile that state/comment mismatch separately. #57 remains open/reopened for integrated efficiency, and WSLc stays on HOLD under #7924.

The 2026-11-10 delayed-request follow-up in the design record found a bounded Xvfb failure for an out-of-band request injected directly by the fixture. It did not capture a late request emitted by the public runtime. The next discriminating check must delay a captured runtime request at the socket/server boundary and verify actual server state, recovery, and fresh-task effect before fixture cleanup.

The subsequent [R04 Fake X discriminator](../../research/integration/public_mcp_fake_x_runtime_wire_late_down_r04_20261110/RESULTS.md) now derives the modeled late state transition from the exact request bytes captured through the public MCP caller. It strengthens request lineage while keeping delivery order and server state explicitly modeled. A server-backed delayed arrival is still unverified.

The separate Win32 operation-owner candidate is a reviewable proposal in
[`../superpowers/specs/2026-10-22-win32-prestarted-supervisor-design.md`](../superpowers/specs/2026-10-22-win32-prestarted-supervisor-design.md).
It is not the X11 supervisor implementation and does not authorize native
input, runtime adoption, or a new allocation. Keep its process-generation,
input-authority, and release evidence distinct from the X11 record above.
