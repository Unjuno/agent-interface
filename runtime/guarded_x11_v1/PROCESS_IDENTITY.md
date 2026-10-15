# Opt-in Linux/XRes process identity

Select this check explicitly on the public scoped Python API:

```python
bridge = NativeHandleBridge(display_name, targets, target, fresh_directory,
                            process_identity=True)
```

This mode requires a trusted local X server with X-Resource 1.2 and a PID
namespace matching the caller's `/proc`. The implementation does not authenticate
that namespace correspondence; qualify it before enabling the mode. Remote X,
container PID namespace differences and XWayland are unqualified. There is no
`_NET_WM_PID` window-property fallback. Missing/ambiguous XRes identity, an
unreadable/mismatched process stat, or a dead process refuses input.

The reader hashes the target XID, server-reported owner PID and Linux process
start ticks with a versioned scheme. Observations retain only the digest in
`pointer_binding.process_generation`; they do not retain the PID/start values.
Only the fixed XRes version handshake is cached, never the owner identity.
The reader requests one resource and the local-PID mask, and requires exactly
one well-formed reply. The server associates that resource with its owner;
the returned canonical client resource base need not equal the window XID
([Xorg implementation](https://raw.githubusercontent.com/mirror/xserver/master/Xext/xres.c)).
The protocol regression parses a real Python-Xlib reply with distinct window
and client-base IDs. Extra records and malformed masks/client IDs refuse.

The digest participates in before/after capture association and target-handle
resolution. A changed or removed digest cannot reuse a previously grounded alias,
even with identical focus, geometry and RGB pixels. Every new key/button press
also checks the digest against the fresh source admitted for that guarded
program, then rechecks the original deadline after the identity lookup. If a
modifier was already pressed, failure prevents the following press and uses the
existing release path. Missing/changed identity at that boundary requires
explicit window review before another program; it does not re-ground or replay.
Releases do not require identity evidence and remain allowed after expiry.

This is sampled **process-incarnation evidence**, not a unique window/client
incarnation or an atomic X-server transaction. Reused resources/connections
within the same process may have the same digest. Changes after the last sample
can race input, and the XRes PID and `/proc` reads are not an atomic snapshot.
The digest does not establish semantic application equivalence,
task success or correctness of a caller-chosen target.

The reads are synchronous. If focus, XRes, `/proc`, XTest/flush or release
verification blocks, input cleanup can still be delayed. This mode adds such
lookups and does not establish bounded release, a watchdog, polling latency,
reliability or efficiency. The independent-cleanup work in
[#17](https://github.com/Unjuno/agent-interface/issues/17) remains required.

Default `process_identity=False` preserves the earlier geometry/focus/pixel
contract and makes no process-identity claim. The public MCP server can select
this policy at startup with `--session-mode guarded-x11 --guarded-process-identity`
([MCP guide](../cli_v1/MCP.md#opt-in-scoped-x11-mode)); individual tool calls cannot
toggle it. Ordinary one-shot CLI and persistent-x11 calls do not select this
option. The portable archive contains the same module and API.

## Validation and provenance

The XRes/PID/start-time approach reuses the idea in preserved research candidate
`50a863b314a3454d6b8e293d9d6523ff943c0808`, with a new public-runtime digest
reader and stricter stat identity checks. Earlier Xvfb or MAP01 results from
other source hashes are not evidence that this caller ran live.

`test_process_identity.py` uses actual handle resolution, public dispatch,
session admission and backend cleanup with Fake X I/O. It checks stable input,
same-XID process changes, capture changes, held-prefix cleanup, unavailable or
malformed proof, deadline consumption, key/button release bypass, legacy mode,
constructor selection and real Python-Xlib protocol serialization/parsing.
The tests use no real display, process identity read, GUI, model or allocation.
`runtime/cli_v1/test_mcp_process_identity.py` also covers explicit MCP startup
selection, raw/delivered digest preservation, actual bridge/handle/session
composition, stale alias refusal, prefix cleanup, result lookup without replay,
and failure without reconnect or policy downgrade, with Fake X only.
They do not qualify a live transport, generation change during a held live
input, finite recovery, independent task effect or full computer control.
