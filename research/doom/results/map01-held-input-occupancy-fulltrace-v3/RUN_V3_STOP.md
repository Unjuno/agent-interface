# Allocation v3 — terminal candidate STOP

Allocation `MAP01-HELD-OCCUPANCY-FULLTRACE-V3-20261002-01` ran once on each
frozen input using candidate SHA-256
`3e95222ac367cd0db85f8a5fd98ba0582623f252da0d5f98067377da3731b6e9`.

- v38 candidate: exit 0; 11 started holds represented in `v38.json`.
- v39 candidate: `STOP_CANCEL_RACES_INPUT_ACK` at `cover-4`, hold step 10.
- Candidate invocations: 2; independent audit: 0; retry: 0.

Exact event clocks from the unchanged v39 raw trace:

- `input_admission.admitted_ns` for `Down`: `55539824242850`.
- cancel command `received_ns`: `55539824423539`.
- `input_admission.input_ack_ns`: `55539824580162`.
- owner verified empty input, cause `cancelled`: `55539837451978`.

Thus admission began before cancel, but its acknowledgement was recorded
156,623 ns after cancel receipt. The second requested key (`space`) has no
admission, no `keys_held` event exists, and there is no observation during this
incomplete hold step. The cancel/refusal semantics do not establish whether
the admitted event reached the application before cancellation; an exact
positive-duration lower bound is not supported. The candidate stopped rather
than assigning a false ordering. This is a cancellation/input in-flight race,
not evidence that no input occurred.

Candidate stderr:
`AssertionError: input acknowledgement after cancellation: ('cover-4', 10)`.
No independent auditor ran because v39 candidate did not finish. Source/input
hashes and pre-registered criteria remain in `FREEZE.md`; no historical raw
data or predecessor allocation was changed.
