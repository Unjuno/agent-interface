# OWNERSHIP COLLISION STOP — duplicate lane, unpooled

Task: `INPUT-OWNER-PHYSICAL-EDGE-TELEMETRY-SOURCE-20260918-002`
Issue: #998
Later branch: `research/input-owner-v12-physical-edge-a630412`
Later claim: `5721439638`
Canonical earlier branch: `research/input-owner-v12-offline-20260918-002`
Canonical claim: `5721423294`
Canonical collision notice: `5721449172`
Canonical pre-primary freeze: `5721632049`
Release comment: `5721733951`

Disposition: `DUPLICATE_PREPRIMARY_UNPOOLED`

- primary scenarios executed: 0
- primary invocations: 0
- reruns: 0
- X11/Xvfb/XTEST/GUI/model/provider/network/task-input/shared-runtime mutation: 0
- excluded construction: 15/15 PASS (diagnostic only)
- source audit: PASS (diagnostic only)
- corruption controls: 5/5 reject (diagnostic only)
- source publication incident occurred before primary; mismatched binary was removed and A2 chunk transport was read back byte-exact.

Nothing from this lane may be pooled into or replace the canonical #998 result.
