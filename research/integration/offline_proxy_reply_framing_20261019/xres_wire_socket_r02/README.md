# XRes QueryClientIds wire exchange through FakeSocketRelay — r02

**Outcome:** `PASS_OFFLINE_XRES_WIRE_RELAY_SCOPED` after a retained fixture-only
failure and correction. The test exercises the documented next discriminator:
real python-xlib `QueryClientIds` request serialization and `ClientIdValue` reply
decoding across a socketpair wrapped by the existing Fake X relay.

The test serializes a request for synthetic window XID 20 using X-Resource
minor opcode 4 and `LocalClientPIDMask`. The fake server checks that the relay
forwards the exact 16-byte request unchanged. It returns one complete XRes reply
frame whose canonical client resource base differs from the window XID; the
relay forwards all 48 bytes unchanged, and python-xlib parses the canonical
base and synthetic PID 123. The updated standard-caller composition fixture
also sends actual XRes `QueryVersion` and `QueryClientIds` frames over the
separate identity socket, decodes their replies with python-xlib, and exercises
the existing guarded MCP caller. Both the wire test (1/1) and caller composition
suite (3/3) pass in normal and optimized Python. The caller suite retains stale
generation refusal before KeyPress and fail-closed `UNKNOWN` after a held reply.
Python 3.11 initially lacked `mcp`, while Python 3.13 lacked `Xlib`; the
composition suite was run with Python 3.13's installed `mcp` and a temporary
copy of the pure-Python Xlib package from Python 3.11. No repository dependency
or runtime source was changed to provision that environment.

## CI-discovered owner-retirement receipt race

The first PR X11 integration run [39246017054](https://github.com/Unjuno/agent-interface/actions/runs/39246017054)
failed in the existing blocked-release Xvfb case: the cancel report said
`owner_process_retired=false` while the same report had `owner_process_exitcode=-15`.
The caller therefore skipped XRes disconnect observation and best-effort
release. The preserved failure receipt is
[`raw/x11-integration-failure-39246017054.json`](raw/x11-integration-failure-39246017054.json).

This exposed a race between the final `is_alive()` sample and the subsequent
exit-code read. `_retire` now treats a non-`None` exit code as definitive child
retirement, keeping the two receipt fields consistent; release remains gated on
the separate XRes disconnect and obligation snapshot. A deterministic regression
test reproduces the sampling order. The full owned-process suite passes 24/24
and the Fake X caller-composition suite 3/3 in normal and optimized Python after
the fix. Updated private-Xvfb integration run
[39246686502](https://github.com/Unjuno/agent-interface/actions/runs/39246686502)
passed all 77 tests, including the blocked-release case. Its exact report and
retained observation image are copied under `raw/` and covered by
`SHA256SUMS`.

This is a scoped fail-closed result, not confirmed caller release: the
independent parent X client read both keys up after the owner release worker's
readback and again at 8.5 s, and observed no delayed `b` KeyPress. However, the
caller receipt remains `release_confirmed=false`, `cleanup_status=UNKNOWN`,
`late_server_request_possible=true`, and `task_success=null`; it required review
and rejected replay. The fix repairs consistent retirement reporting and
reaches the bounded cleanup path, while the current contract still refuses to
certify cleanup when a server request may remain. This passes safety assertions,
not the bounded-release objective.

The first run failed because the synthetic `ClientIdValue` size field was set
to `1` (a byte count) instead of `4`; python-xlib consequently parsed an empty
value and left the four PID bytes unconsumed. That fixture failure is preserved
in [`raw/initial-fixture-failure.txt`](raw/initial-fixture-failure.txt). After
correcting only the fixture size field, the test passed 1/1 in normal Python
and 1/1 with `-O`. The test code, conditions, failure, exact query/reply bytes,
and both outputs are covered by [`SHA256SUMS`](SHA256SUMS).

## Scope and next decision

This is one synthetic protocol/relay construction check plus one existing
private-Xvfb standard-caller cancellation test. It establishes that
the existing framing relay can transport the real encoded XRes request/reply
shape without corrupting it and that the pinned python-xlib parser recovers the
canonical client base and PID value. It does not test malformed XRes payload
handling, a real X server's extension negotiation, live process discovery,
live connection ownership or server ordering, blocked-I/O release, physical
input release, independent application effect, task success, recovery, or
efficiency. The standard-caller composition now uses real encoded XRes
transactions over a Fake X socket, but still supplies synthetic server replies
and a synthetic `/proc` identity. The Xvfb test has a synthetic application,
test-injected delayed request, and independent keymap readback; it does not
certify the caller's cleanup receipt. The next discriminator is a separately
authorized private-Xvfb/live-server composition check with exact server
extension negotiation and owner-release observation; it remains gated on
current allocation and environment custody.

## Existing private-Xvfb target-generation composition

The same X11 integration run also passed
[`test_process_and_window_generation_flow_through_standard_mcp`](https://github.com/Unjuno/agent-interface/actions/runs/39246686502).
The raw report and observation PNG are retained under
[`raw/x11-generation-39246686502/`](raw/x11-generation-39246686502/). An
independent XRes `QueryClientIds` returned the synthetic app's PID; the test's
independent `/proc` start-ticks calculation exactly matched the generation
hash returned by standard-caller observation. The test then invoked input,
observed app property `[1]` and the matching KeyPress/KeyRelease through
independent clients, confirmed the runtime release receipt and independent
key-up readback, destroyed the target window, and verified that the next
standard-caller input was refused before dispatch with review required.

This is meaningful integrated evidence for target identity, target lifecycle,
effect ordering, and release in one X.Org Xvfb synthetic-app task. It does not
establish MAP01/game task success or native desktop/XWayland behavior, and the
runtime's `task_success` field remains null. The assertion of `[1]` is a
test-local synthetic-app oracle, not a runtime task-success receipt. The exact
report and image hashes are included in `SHA256SUMS`.

No WSLc, Docker, network, live X server, GUI, OS input, model, or allocation was
used. No task-success or physical-release claim is made.

## Reproduction

Run from repository root with python-xlib installed:

```powershell
$env:AGENT_INTERFACE_XRES_WIRE_RAW_DIR = "research/integration/offline_proxy_reply_framing_20261019/xres_wire_socket_r02/raw-normal"
python -m unittest -v research.integration.offline_proxy_reply_framing_20261019.xres_wire_socket_r02.test_xres_query_socket
$env:AGENT_INTERFACE_XRES_WIRE_RAW_DIR = "research/integration/offline_proxy_reply_framing_20261019/xres_wire_socket_r02/raw-optimized"
python -O -m unittest -v research.integration.offline_proxy_reply_framing_20261019.xres_wire_socket_r02.test_xres_query_socket
$env:PYTHONPATH = "<directory containing the pure-Python Xlib package>"
$env:AGENT_INTERFACE_FAKE_X_COMPOSITION_RAW_DIR = "research/integration/offline_proxy_reply_framing_20261019/xres_wire_socket_r02/caller-normal"
py -3.13 -m unittest -v runtime.cli_v1.test_mcp_relay_composition
$env:AGENT_INTERFACE_FAKE_X_COMPOSITION_RAW_DIR = "research/integration/offline_proxy_reply_framing_20261019/xres_wire_socket_r02/caller-optimized"
py -3.13 -O -m unittest -v runtime.cli_v1.test_mcp_relay_composition
```
