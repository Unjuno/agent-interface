# Test-only socket relay result

**Disposition:** `PASS_FAKE_RELAY_CONSTRUCTION_SCOPED`.

This addendum completes the prior packet's next offline discriminator. It wraps
the existing X11 framing candidate with `fake_socket_relay.py` and three
process-local `socketpair()` channels: a caller stream, a fake upstream, and a
separate synthetic event-receipt channel. The relay accepts already-established
tracker state and opens no socket of its own.

## Observed behavior

- An ordinary unmatched `GetPointerControl` reply is forwarded when no matching
  independent event receipt exists.
- A separate receipt with the matching action ID, `KeyPress`, and keycode gates
  the selected reply. The relay buffers that reply and later server frames in
  stream order, then retires at the configured 150 ms deadline with
  `release_state=UNKNOWN`, `task_success=null`, and replay disabled.
- Fake-upstream EOF while a reply is held retires promptly with the same
  `UNKNOWN` terminal semantics. A non-reading client causes bounded
  `backpressure_limit` retirement. A 64 KiB valid server stream is forwarded
  intact when a client is actively draining it.
- Once a reply is held, a server parser error also keeps malformed later bytes
  behind it until timeout; parser fallback cannot reorder the stream.
- A malformed client frame disables parsing and preserves the exact bytes to
  the fake upstream. Parser/relay errors do not create a release or success
  claim.

Test-first regressions reproduced a false backpressure retirement on a large
but drainable stream, a stream-order violation where later server frames passed
a held reply, and a parser-error fallback that could bypass the hold. Each
pending buffer now flushes or retires at its configured bound. Once a reply is
held, all later frames, including malformed bytes, remain behind it until
retirement.

## Validation and limits

On Windows Python 3.11.9, the existing parser/specification tests plus the new
socket tests passed 27/27 in normal mode and 27/27 under `-O`. Exact output is
preserved in [`raw/fake-relay-test-normal.txt`](raw/fake-relay-test-normal.txt)
and [`raw/fake-relay-test-optimized.txt`](raw/fake-relay-test-optimized.txt);
conditions are in [`fake-relay-conditions.json`](fake-relay-conditions.json).
[`FAKE_RELAY_SHA256SUMS`](FAKE_RELAY_SHA256SUMS) binds the new sources, tests,
conditions, outputs, and parser implementation.

This is a local socket-pair construction test. It does not connect the relay to
the standard MCP caller or a real X server, inspect OS input state, establish
physical release, validate application effect, or prove a hard release-time
guarantee. `UNKNOWN` is the only terminal release classification when the
selected reply is withheld. It did not use WSLc, Docker, network access, a GUI,
OS input, a model, or a live allocation. A02/A03 and their first outcomes are
unchanged.

## Next boundary

Next, test whether this framing and owner-retirement seam can be composed through
the existing guarded standard caller using only Fake X sockets: include the
separate process-identity connection, target-generation binding, cancellation,
held-input obligation custody, and independent synthetic effect receipt. Keep
physical release and task success `UNKNOWN` until the real backend has separate
qualifying evidence. Do not attempt a live run unless an unused allocation and
the explicit WSLc owner gate are independently verified.
