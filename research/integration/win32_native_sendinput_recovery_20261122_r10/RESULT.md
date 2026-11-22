# Win32 R10 — excluded pre-dispatch readiness stop

**Disposition: `EXCLUDED_PRE_DISPATCH`; experiment acceptance: FAIL/NOT REACHED.**
R10 used frozen current-main source `745ffe22e02af08e65eca4d638beb998384ae7a8`
and stopped at its owned-fixture readiness gate before starting the public MCP
server or dispatching input. The first outcome is retained; there was no retry.

The failure message was `fresh owned fixture/foreground/SHIFT-up preflight
failed; no input sent`. The raw native key-state read returned `shift_down: null`
with an empty witness list, so the test could not establish neutral input state
before action. The runner does not retain each readiness predicate separately
when that guard fails; do not infer that focus alone caused the stop. The exact
fixture journal contains only `ready`; there is no effect file, public
observation, dispatch, or call ID. Cleanup evidence records fixture exit code
0 and restoration of the foreground window value sampled at cleanup.

The pretrial source/condition manifest has 20 entries with no mismatch. The raw
manifest covers five run files with no mismatch. The independent stop audit
passes all seven custody/exclusion checks and explicitly records
`experiment_acceptance_pass: false` in `audit.json`.

## Next adjustment

Before a new attempt, explicitly activate the newly created owned fixture and
record the activation result, `GetForegroundWindow`, and a boolean native
SHIFT-up readback with a nonempty query witness. If any preflight predicate
remains unknown, stop before public observation or dispatch. This is a setup
repair for a new attempt ID; R10 remains immutable and excluded.

The current-main expiry/recovery trial itself remains untested. R10 provides no
evidence for deadline rejection, post-expiry cancellation, release latency,
late-input horizon, generation fencing, task success, reliability, or Issue
#57 closure.
