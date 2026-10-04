# MAP01 v39 pre-input exception cleanup

**H — Hypothesis:** When v39 rejects a typed health source before admitting the next cover program, the controller can preserve the original failure and still request the child session's normal finish path, retain the post-control score and owner-close receipt, and record whether all accepted programs have verified empty-release terminals and both child and planner shutdown completed.

**T — Minimum discriminator:** Fault-inject the pre-input gate failure through the actual v39 exception handler with inert process/planner boundaries. Independently exercise the cleanup helper with a running child, an accepted program with verified empty-release terminal, an orphan accepted program, and failures in score wait, process wait, and planner close. PASS requires the original exception identity to survive, a `controller-failure.json` to name the failing stage, and cleanup evidence to distinguish fully closed from incomplete teardown.

**D — Result:** PASS for three local stdlib tests, Python compilation, and `git diff --check`. The tests cover successful finish/score/child/owner closure, multiple cleanup failures without replacing the primary exception, and actual v39 handler wiring/re-raise. This is construction evidence only; no VizDoom, app-server, model, GUI, or input operation ran.

**C — Competing explanation:** The constructed process and owner records do not reproduce native child pipe pressure, a real scorer/backend failure, or a non-cooperative session. A successful finish request does not itself prove that an earlier input program had terminated.

**U — Uncertainty:** The helper is deliberately wired only around `build_cover_monitor`, which runs before the next program is admitted. It does not repair exceptions during active input, does not independently verify physical input release, and does not guarantee planner-child termination beyond the client close contract. The separate stderr-capture change remains unmerged.

On cleanup, v39 writes `controller-failure.json` before and after teardown. `cleanup_complete` requires a post-control score event and file, child exit, successful planner close, verified owner records ending in `reason=close`, and an empty verified release terminal for every accepted program observed by the parent; otherwise the status is `cleanup_incomplete`. The initiating exception is re-raised unchanged and cleanup failures are attached as notes and retained in the report.
