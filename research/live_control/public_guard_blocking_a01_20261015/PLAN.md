# Public guarded X11 blocking characterization

Baseline main: a812e7881eba39c9f041ff11308853630b1fe8f1. Ordinary offline
construction only, using the user's Fake X scope. No GUI, X connection, physical
input, model, Docker/WSLc or allocation will be used.

- H: the public dispatch/session and guarded backend still cannot release a held
  modifier while the second key's focus query is blocked. A blocked release sync
  can instead leave the fake bitmap empty while no verified result has returned.
- T: three fixed cases: healthy, second-focus-query block, cleanup-sync block.
  Use the real dispatch, core admission, session, execute, key emission ordering
  and release logic. Stub platform preflight, focus observation, key mapping and
  the X connection. Advance a fake clock to the original expiry only after the
  named boundary is reached. Always unblock/join the worker in cleanup.
- D: characterize only if healthy completes verified-empty, focus block retains
  CTRL past expiry without a returned receipt, cleanup sync has fake empty state
  without a returned receipt, both blocked cases reject a new `a` press after
  expiry and eventually return execution_failed with verified cleanup. Record
  all emissions and the full public result. Run normal/optimized Python once
  each after source freeze; retain any failure rather than replacing outputs.
- C: Fake X state is inspectable test memory, not independently measured OS or
  application state. The bridge owner/visual checks and backend preflight are
  stubs. No cancellation API is invoked; the source interface has no cancel
  method on X11RuntimeSession, so no cancel reachability claim is made.
- U: thread scheduling caps are harness limits, not physical release deadlines.
  This does not implement a guardian, test a stopped X server, establish target
  generation, live recovery, task success or efficiency. The result must guide
  the next repair; it cannot satisfy the live gate by characterization alone.
