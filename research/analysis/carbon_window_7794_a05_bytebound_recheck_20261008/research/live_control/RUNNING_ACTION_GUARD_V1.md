# Running action guard v1

V33 revalidates a planner-authored action immediately before its first Executor
submission. A primary MAP01 action can still contain several commands, and one
held-input command can last up to 900ms. The runtime already captures exact
observations about every 50ms during a hold, but v33 only collects those frames
for posthoc visible-effect receipts.

`running_action_guard_v1` makes those existing observations actionable without
adding an image, model call or input operation. It binds the exact action and its
original contract, and deterministically re-evaluates health, ammunition,
focus/surface/geometry, sequence and freshness while an Executor program is
active. A valid observation preserves already admitted authority. It never
creates or renews authority.

If evidence becomes invalid during input, the guard enters `CANCEL_REQUIRED`
and immediately represents current authority as false. A caller must issue a
matching cancellation and return a cancelled terminal with independently
verified empty keys/buttons before the guard reaches
`REVOKED_ACTION_NOT_CURRENT`. Between program segments, a completed terminal
requires another strictly newer valid observation before the next acceptance.
An invalid inter-segment observation rejects the remaining action without a
cancel because no program is active.

Ten deterministic tests cover valid continuous operation, health and ammunition
breaches, focus change, non-monotonic evidence, inter-segment revalidation,
verified release, final completion and forged evidence. This is a model-free
state-machine construction. It has not yet cancelled a live program, measured
cancel latency, improved gameplay or reduced model latency. The next integration
must preserve v33 and add the guard to a separately versioned controller, using
the exact observations already emitted by each hold.
