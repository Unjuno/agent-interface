# Additive-path recovery of the #3633 formal-01 STOP

The original #3646 branch used
`research/integration/issue_2499_readiness_successor_3633_v1/`, a path already
occupied on main by merged PR #3639. The two records are distinct allocations
and must not share or overwrite that directory:

- Main's existing record is `issue3633-readiness-identity-v4-formal-01`, on
  image `sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`,
  later corrected to `HOLD_PROCESS_LIFECYCLE_UNVERIFIED` because Calc's owner
  PID was not reconciled.
- The rescued record is `issue2499-readiness-successor-3633-formal-01`, on
  image `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f`.
  It stopped earlier at `STOP_IDENTITY_MISSING`, before any transition or
  input, with one invocation and zero retries.

The PR files were copied by Git object identity from source head
`2ba732b171e48704c0244e89032fc2c073541304` into this new sibling directory.
Frozen files, result bytes, and source hashes are unchanged. No STOP was
replayed, combined, or reclassified. The 7 readiness tests and freeze-integrity
check were rerun in the pinned image with network disabled, read-only root and
source; no formal invocation was performed during recovery.

Issue #3633 remains open pending the linked #3645 successor. This note records
why the original same-path PR is superseded and preserves the distinct STOP for
future integration and audit.
