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

The first run failed because the synthetic `ClientIdValue` size field was set
to `1` (a byte count) instead of `4`; python-xlib consequently parsed an empty
value and left the four PID bytes unconsumed. That fixture failure is preserved
in [`raw/initial-fixture-failure.txt`](raw/initial-fixture-failure.txt). After
correcting only the fixture size field, the test passed 1/1 in normal Python
and 1/1 with `-O`. The test code, conditions, failure, exact query/reply bytes,
and both outputs are covered by [`SHA256SUMS`](SHA256SUMS).

## Scope and next decision

This is one synthetic protocol/relay construction check. It establishes that
the existing framing relay can transport the real encoded XRes request/reply
shape without corrupting it and that the pinned python-xlib parser recovers the
canonical client base and PID value. It does not test malformed XRes payload
handling, a real X server's extension negotiation, live process discovery,
live connection ownership or server ordering, blocked-I/O release, physical
input release, independent application effect, task success, recovery, or
efficiency. The standard-caller composition now uses real encoded XRes
transactions over a Fake X socket, but still supplies synthetic server replies
and a synthetic `/proc` identity. The next discriminator is a separately
authorized private-Xvfb/live-server composition check with exact server
extension negotiation and owner-release observation; it remains gated on
current allocation and environment custody.

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
