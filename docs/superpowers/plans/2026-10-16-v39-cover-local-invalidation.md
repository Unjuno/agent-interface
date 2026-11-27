# Cover release before planner acknowledgement

Goal: remove the reproduced planner-ACK dependency from failed cover-release
classification, without another input writer or an unbounded worker per request.
This implements the remaining seam from #8956; FINAL v5 authorizes this repair.

- Separate local answer invalidation from remote interrupt-request accounting in
  `persistent_planner_adapter_v2.py`. Preserve matching handles, duplicate-request
  refusal, stale-answer rejection and the aborted-transport fence.
- In V39 invalidated-cover cancellation, invalidate locally, write/flush cancel,
  inspect the terminal and require current strict known-empty release. Only a
  healthy release proceeds to synchronous remote interrupt.
- Save failed terminal/local invalidation before planner abort, preserving an
  existing output and the primary error if save/abort also fails. Actual main's
  three invalidated-cover callsites supply `args.out`.
- Verify healthy/cancel-write races, stale handles, ACK blockage, save collisions,
  abort faults, and actual selected Executor/V4/V12 with Fake X release send held.
  Retain first RED and all intermediate failures. Include affected adapter and
  strict receipt tests in the isolated normal/-O regression entry.
- Integrate the reviewed exact head against current main using existing CAS.

Limits: input send/flush, terminal absence, scheduler, filesystem and transport
close are not proven hard-time bounded. Healthy planner ACK and other fatal
terminal paths still require their own qualification. This is no live allocation,
physical release, process IPC, replacement authority or task-recovery claim.
