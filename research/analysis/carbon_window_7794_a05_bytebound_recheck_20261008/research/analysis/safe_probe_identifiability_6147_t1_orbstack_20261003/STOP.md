# Formal allocation STOP — AI-6147-T1-ORB-X11-20261003-01

Disposition: `STOP / NOT_EVALUATED`. This is not a hypothesis failure or pass.

Exactly one candidate container was invoked (adaptive arm); the independent auditor was not invoked. The candidate emitted 10/10 expected-shaped rows, and the fixture emitted 44 oracle rows ending in `FIXTURE_END` with exit 0. However, candidate exit was 1: while closing the Xlib display, it received `Xlib.error.ConnectionClosedError: Display connection closed by server`. Candidate inspect reports `OOMKilled=false`; fixture inspect reports exit 0 and `OOMKilled=false`. The runner therefore stopped as frozen at the first nonzero candidate exit. The two remaining candidate arms and auditor were never invoked. No retry, tuning, or replacement execution was made under this allocation.

The captured rows appear to cover the planned adaptive choices, but they were not accepted as formal evidence: the allocation gate includes a clean candidate process exit and independent raw-only audit. No semantic hypothesis conclusion can be drawn from these bytes. Preserve all raw data and the runner stop line in `raw/formal_01/`; do not rerun this allocation. A future successor must separately preregister any lifecycle correction and new allocation before execution.

The failure is consistent with a fixture/client teardown race: the fixture finishes and closes Xvfb after emitting all ten cases, while the candidate's `controller.close()` flushes the now-closed display. This is a diagnosis of the captured stack and process states, not proof that any hypothesis arm passed.
