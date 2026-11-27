# A16 — soft versus hard ammo change during pending inference

**H:** With source ammo 6 and the current cover monitor's hard floor 1, an in-epoch ammo change to 4 while a planner turn is pending remains a soft event: the existing monitor does not interrupt the pending turn, the adapter returns an eligible answer, and fresh action admission rejects a synthetic action authored with minimum ammo 5. A change to 0 crosses the cover hard floor: the actual monitor requests a new decision, the adapter is interrupted before a wire-completed answer can become eligible, and no action reaches final admission.

**T:** Freeze exact current-main controller/monitor/adapter sources. For each arm, begin the same planner request from ammo 6, deliver one newer typed observation during the fake client's pending wait (ammo 4 or 0), run actual `DoomCoverSignalPairMonitor.observe`, and if it invalidates call actual adapter `interrupt` before returning a completed fake response. In the soft arm run the actual final-action admission helper. One WSLc CPU container run.

**D:** PASS for the scoped boundary if ammo 4 preserves an eligible turn but rejects the returned minimum-5 action, while ammo 0 invalidates, interrupts and makes a subsequently wire-completed answer ineligible; neither arm admits an executor or grants authority.

**C:** This outcome follows the explicitly authored cover floor and action minimum predicates. It does not show the floor is behaviorally correct or that cancellation produces safe physical release.

**U:** Deterministic fake client, synthetic response, and typed observations. No real model, game, input, physical release, recovery, task effect, or live allocation. Construction-only.

Base: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
