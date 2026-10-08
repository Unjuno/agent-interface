# V39 adapter natural-completion race A01

This deterministic software-boundary experiment tests a completion race distinct from the cancel-to-release handoff. On current `main` (`286b4e197cf2cf1cdceea18ca65c2c0bb95c8c52`), it injects a matching `turn/completed` notification after the planner interrupt request is written but before its correlated response arrives.

Result: `PASS_COMPLETION_RETAINED_BUT_ANSWER_INVALIDATED`. The completion is collected while the interrupt response is pending. The returned turn status remains `completed`, but cancellation is recorded, `answer_eligible` is false, and no answer is exposed. Executor-cancel flush precedes the interrupt request. See `RESULT.json` for event order and source blob identities.

Reproduce from the experiment root with `python run_race.py`. The prior cancellation/handoff regression suite was also rerun against its frozen source revision: six tests passed.

Scope: AST-extracted current-main adapter/client methods with a deterministic in-memory transport and notification schedule. This validates software event handling only. It does not measure OS-level release, physical key state, live HUD-triggered interruption, useful game feedback, recovery, MAP01 task effect, or production timing. No game, model, GUI, or OS input was used.

The required Issue #59 fresh live threat-exposure gate remains outstanding; current main records its live-game lane as unassigned.
