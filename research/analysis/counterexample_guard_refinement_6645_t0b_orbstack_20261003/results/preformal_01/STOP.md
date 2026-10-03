# A02 launch STOP

The corrected source passed its OrbStack construction suite 13/13, but the
formal launch command used a truncated image digest and `docker create` exited
1 with `invalid checksum digest length`. No container or candidate/auditor
process was created; no raw formal output exists. This is an operator launch
error, not a scientific FAIL. Allocation 02 is stopped and will not be retried.
The precise command and observed stderr are in `STOP.json`.
