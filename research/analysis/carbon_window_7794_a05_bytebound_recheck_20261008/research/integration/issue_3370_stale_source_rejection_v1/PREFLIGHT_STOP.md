# Preflight allocation STOP — retained unchanged

This is the first preregistered allocation attempt, not a stale-input result.
OrbStack successfully started Inkscape, returned initial sequence 1 and
committed the explicit read-only stage-1 observation, which returned sequence
2. The initial and later PNG hashes were identical because the visible canvas
did not change; source identity advanced despite identical pixels.

The test client expected `status=boundary` at the MCP response top level. The
compact observation-reference format places that status at
`receipt.native_result.status`; the client therefore stopped before making
the planned stale stage-2 call. No stage-2 request or `actions.json` exists.
The MCP stdio client then exited, which terminated the managed owner without a
normal task finish. Cleanup/owner-exit evidence is incomplete. Disposition:
`STOP_OBSERVE_RESPONSE_SHAPE`, no retry within this allocation. Raw output is
retained under `evidence/stale_source/` and is excluded from any success count.

A separate preregistered allocation may test the same hypothesis after teaching
the client to read the pinned compact receipt schema. It must not reuse this
allocation or reinterpret this STOP.
