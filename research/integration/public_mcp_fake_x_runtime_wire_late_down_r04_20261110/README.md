# Public MCP Fake X captured-request late-down discriminator R04

Status: preregistered bounded construction experiment; not a live X-server result.

## Question

Can the existing public-MCP Fake X composition retain the exact XTEST KeyPress
bytes emitted by the runtime, preserve them across the cancellation/release
readback boundary, and derive the later modeled key state from those bytes?

## Frozen source and conditions

- Source commit: `5b5194a24ea334f7be3c49aa69209aae44531ea2`.
- Test: `runtime.cli_v1.test_mcp_relay_composition.StandardMCPRelayCompositionTests.test_standard_owned_caller_keeps_unknown_after_fake_late_down`.
- One run in normal Python 3.13 and one run under `-O`; no retries.
- The public standard MCP caller emits the KeyPress through its normal guarded
  input path. The Fake X upstream captures the complete 36-byte XTEST request.
- After the existing separate cleanup readback reports keys up, the test
  decodes the captured request's event type and keycode and applies that input
  to a test-owned key-state model. The delivery order and server state are
  modeled; this is not a live X server or delayed socket delivery.
- Primary assertions: bytes are a complete XTEST FakeInput KeyPress; the
  decoded keycode matches the captured receipt; release readback precedes the
  modeled delivery; final modeled state reflects the applied press; runtime
  cancellation remains UNKNOWN and replay stays denied.
- No live GUI, WSLc, Docker, external model/provider, network, or OS input.

## Limits

This tightens evidence lineage from public runtime output bytes to a bounded
Fake X state transition. It does not establish that an old X server connection
can deliver a request after its client process retires, nor measure live X.Org
queueing, physical release, product task success, MAP01, efficiency, or broad
reliability. A live/private-Xvfb server-ordering study remains separate.
