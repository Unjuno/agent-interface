# Allocation v2 — terminal candidate STOP

Allocation `MAP01-HELD-OCCUPANCY-FULLTRACE-V2-20261002-01` was executed once
per frozen input with the candidate hashes in `FREEZE.md`.

- v38 candidate: exit 0; 11 hold rows retained in `v38-v2.json`.
- v39 candidate: `STOP_UNMODELED_PARTIAL_INPUT_ADMISSION` at `cover-4`, hold
  step 10; no v39 output was emitted.
- Candidate invocations: 2; independent auditor: 0; retry: 0.

The v39 raw trace shows the requested keys `Down + space`, a `Down`
`input_admission` / acknowledgement at `55539824242850` /
`55539824580162 ns`, then cancellation before `keys_held` or the second
`space` admission. The active input owner verified an empty set with cause
`cancelled` at `55539837451978 ns`. This is not zero-input. It is a partial
key acquisition with no observation during the incomplete acquisition.

The candidate correctly refused to classify that interval using the full-hold
path. Do not reinterpret the v38-only output as a complete v2 result and do
not run the v2 candidate again. A distinct successor may use a conservative
zero lower bound and a verified-release upper bound for this specific partial
admission shape; other partial/unacknowledged states must still stop.

The candidate stderr was the exact assertion:
`AssertionError: partial/unacknowledged input needs a separate bound: ('cover-4', 10)`.
Frozen source and input hashes remain in `FREEZE.md`.
