# MAP01 running action controller v34

V34 preserves v33 and attaches `running_action_guard_v1` after the immediate
pre-admission result becomes `VALID_CURRENT`. Exact observations already emitted
during each held-input program are converted to health/ammo snapshots and checked
against the same source, binding, freshness and predicate contract.

If an active primary or fallback program becomes invalid, the controller sends a
matching cancel, waits for a cancelled terminal, and requires independently
verified empty keys/buttons. It records the partial command, keeps completed
effect receipts, discards the remaining action, and executes no later segment.
When a completed program boundary requires a primary continuation or fallback,
the controller runs one passive `observe` program; only a strictly newer valid
snapshot permits the next input program.

The separately frozen live v2 probe exercises the active single-primary path
with no contingency. Real visible ammo48→47 invalidates held fire and reaches
empty release138.694ms after the invalidating capture.

Two composition limits remain before a planner-driven v34 successor can run.
The final-admission-v2 receipt retains historical first acceptance and does not
itself incorporate the later running-guard state; consumers must currently read
both receipts. Also, the action fingerprint covers the primary command list.
Fallback programs are selected from the validated planner output and share the
same state predicates, but the running receipt does not independently bind each
submitted fallback motor payload. A v35 composition must bind every program
payload and expose one unambiguous current-authority state.

V34 has not called the model or run a planner-authored schema-v6 action. Preserve
the v34 hash used by both live probe allocations and version the composition fix.
