# Results: public MCP captured-request Fake X discriminator R04

## Outcome

`PASS_FAKE_X_CAPTURED_REQUEST_MODEL_ONLY` in normal and optimized Python 3.13
(1/1 each). The test is from source commit
`5b5194a24ea334f7be3c49aa69209aae44531ea2` and source SHA-256
`066a843f8fd188477208ca7d8e8f4864d92bc823849ba5a4b50eff79d2c15f58`.

In both runs, the standard guarded MCP caller emitted a complete 36-byte XTEST
FakeInput KeyPress request through the existing Fake X socket composition. The
retained downstream receipt and the later state-model delivery contain the
same exact request bytes. The test decoded event type KeyPress and keycode 2
from that request. The injected separate cleanup readback was event 1 and
reported all keys/buttons up; the modeled delivery was event 2 and changed the
modeled key state to keycode 2 down.

The runtime cancellation receipt remained `cleanup_status=UNKNOWN`,
`release_confirmed=false`, `task_success=null`, and `replay_allowed=false`, with
`late_server_request_possible=true`. The terminal action result was
`runtime_failed`. No success or release claim was promoted.

## Interpretation

This improves lineage over the prior late-down case: the post-readback Fake X
state transition is now derived from the exact KeyPress bytes captured from the
public MCP runtime, rather than from a separately hard-coded event/keycode.
Both the delivery order and the resulting server state are still test-model
inputs. There is no live X server, socket-level delayed delivery, or observed
server-side transition here. In particular, this does not show that a request
can arrive after its X client process retires. The next gate remains a private
Xvfb or protocol-server composition that delays the captured request across
actual client retirement, then records server state, recovery, and a separate
fresh-task effect before cleanup.

No live GUI, WSLc, Docker, network, model/provider, OS input, MAP01, efficiency,
or reliability population was used. Per-arm raw JSON and exact test output are
under `raw/`; `SHA256SUMS.json` binds the packet.
