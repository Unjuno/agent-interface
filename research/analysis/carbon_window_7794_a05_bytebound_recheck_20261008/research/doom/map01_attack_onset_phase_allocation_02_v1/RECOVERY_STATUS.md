# Recovery status — allocation 02

This package preserves the exact preformal freeze, bundled source, environment,
and import-only readiness receipts from the original branch. The recorded
state is `IMPORT_ONLY_PREFLIGHT_PASS_PENDING_GITHUB_READBACK` with
`formal_authorized: false` and `formal_invocations: 0`. The import-only gate
reported `science_sessions=0` and `physical_inputs=0`.

Publishing this archival package does not retroactively authorize the frozen
eight-session onset allocation. No Doom game session, model, scientific case,
or physical input was run during recovery. The predecessor allocation-01
STOP and later allocation-03/04 and T6-T10 startup-gate evidence remain
separate; no results are pooled or replaced.

The original preflight attempt history, including intermediate setup errors,
is retained verbatim in `PREFLIGHT_RESULT.json`. No formal result is claimed.

## Local recovery check

The frozen v12 `InputOwner` construction unit suite was independently rerun
once in the already-cached pinned image `sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed`
(`linux/amd64`, network disabled, read-only root/source mounts): 10/10 passed.
The comparator `input_owner_v10.py` was verified against its declared Git blob
`341b3c01649943ddaad5f28431a792c4889cc36e` from commit
`3c34e3cea2a39e961e097b41444ff4a7563a4170`; runtime dependencies came from the
declared runtime source commit `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`.
This is unit-test evidence only: no X server, game session, candidate, auditor,
model call, or physical input was launched.
