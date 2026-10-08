# Independent audit self-check correction

The first invocation of `audit_startup.py` failed one auditor assertion for the
`v15-default` route: it assumed `cached_owner_file` should equal the selected
backend's `owner_file`. That assumption was too strict. The selected backend is
`input_transition_owner_v4.InputOwner`, while its underlying cached raw owner is
`research/live_control/input_owner_v12.py`; this split is expected for the
default V15 route.

The assertion was corrected to check the route-specific expected cached module.
The independent readback audit was then rerun and passed. This was an auditor
logic correction only; no startup probe, candidate, owner, or input operation
was rerun. The first failing script bytes and stdout were not preserved, so this
note records the failure from the tool output and the changed assumption rather
than claiming exact source custody.

The final `audit_startup.py` and `audit-result.json` remain unchanged. The
startup results establish module/source selection only. They do not instantiate
an owner or execute UP. The missing UP telemetry conclusion is source-derived.
Routing through V4 alone may provide its transition receipt, but does not by
itself establish the A01 physical-edge sampling contract; a compatible adapter
must preserve current release safety and the V15 batch/pending-release guards.
