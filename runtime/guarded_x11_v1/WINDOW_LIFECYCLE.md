# Opt-in direct-window lifecycle evidence

Use `NativeHandleBridge(..., process_identity=True, query_worker=True,
window_lifecycle=True)` or start the standard MCP server with:

```text
--session-mode guarded-x11 --guarded-process-identity --guarded-query-worker --guarded-window-lifecycle
```

`create_server(..., guarded_window_lifecycle=True)` selects the same policy;
`session.window_lifecycle` reports it. Tool calls cannot toggle it. Dependencies
are checked before opening a session. Defaults retain the process-only contract
and its same-process reuse limitation. This option is Fake X construction-qualified,
**not live-qualified**.

The persistent read-only query client selects `StructureNotifyMask` on the
target itself, confirms `your_event_mask` after a round trip, and drains at most
256 events per read. Newly watched XIDs get opaque random 64-hex tokens scoped to
this reader. These are continuity tokens, not server-issued lifetime identifiers.
Unmap/map, configure, gravity, circulate and reparent preserve continuity.
Destroy, unexpected/malformed/synthetic events, lost subscription, transport failure
or queue-budget exhaustion permanently retire lifecycle reads. There is no rearm
on the same XID. Different readers get different tokens. MappingNotify, delivered
independently of window subscriptions, does not itself invalidate continuity.

`pointer_binding.window_generation` accompanies the process digest. Capture and
qualification are bracketed by the same lifecycle reader. Handles reject changed/
missing tokens. The retained source is checked again before each new key/button
press or activation request. Releases bypass lifecycle reads. Failure requires
closing the session and reviewing a fresh source; old aliases are not renewed.

Idle lifecycle requests have a one-second local read budget. Active requests keep
the original action deadline/cancellation fence. Late answers are discarded and
the query client closes on its own thread after the read returns. It does not
reopen automatically or interrupt native I/O.

`observation_worker=True` / `--guarded-observation-worker` remains supported.
Its raw `isolated-observations/observation-N.json` precedes lifecycle qualification.
Additional `qualified-observation-N.json` records contain the token transported
into owner history and MCP results. Qualification persistence uses the visual
worker and original action deadline/cancellation. Raw persistence alone is not
qualified delivery.
Qualified files are also intermediate records: a late save may remain after
cancellation. Only the subsequent owner-history publication and delivered
receipt establish observation publication; file existence does not certify it.

The assumptions are a trusted local X server, reliable ordered connection,
honest native events, and exclusive use of this query connection by its reader.
Arbitrary undelivered events, hostile servers and atomic check/use with XTEST
are not covered. Destruction immediately after the last sample remains a race.
This supplies rejection evidence, never input authority.

Direct subscriptions follow X11's
[DestroyNotify and ReparentNotify semantics](https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html).
Historical root-only [#3950 evidence](../../research/integration/same_client_window_lifecycle_v1/README.md)
remains research-only; its producer was not rerun/promoted. Native subscription/
reparent/toolkit behavior, performance, physical release, bounded task recovery
and independently scored effects need separate evidence.

Fake X tests cover the actual query worker, MCP owner, bridge, handles,
dispatch/session and release path: process-only stale acceptance as a control,
selected stale rejection, prefix release, blocked cancellation/expiry and late
retirement, visual isolation, capture-time destruction and activation fencing.
They use no GUI/input/model/WSLc allocation and do not complete #5/#17/#59/#57.
