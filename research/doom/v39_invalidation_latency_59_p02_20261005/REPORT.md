# Post hoc result: visible-threat health invalidation

**Disposition: one historical mechanism observation; not a fresh current-main allocation.**

The pinned live run used the fixed `map01-threat-contact-v2` fixture. In decision 5, `cover-5` contained `retreat_fire` while the planner waited 8.916 seconds. The start observation (sequence 166) showed health 61 and ammo 40, with no hostile visible in that viewport. A hostile was visible by sequence 200 during the wait. Health was 51 and ammo 38 at sequence 200, remained at the health floor 51 at sequence 217, then read health 48 and ammo 37 at sequence 218 while the hostile remained visible.

The authored health floor was 51. Sequence 218 crossed below it. The typed frame was captured 8.723 seconds after model start; the guard evaluated `HARD_INVALIDATED/below_hard_minimum` 37.051 ms before planner terminal. The cover cancellation then verified empty keys and buttons before terminal closure. The planner ended interrupted and ineligible, and no primary plan was admitted. Independent episode score: 1 kill, 0 deaths, no MAP01 exit.

| Gate | Evidence in this trace | Limit |
|---|---|---|
| Visible hostile during pending wait | Exact paired frames show one by sequence 200 and at trigger sequence 218 | One analyst visual review; no automatic threat classifier |
| HUD guard crossing | Health 51 at sequence 217, then 48 at 218; floor 51 | Health-loss cause is not identified |
| Stop before planner terminal | Guard evaluation precedes terminal by 37.051 ms; answer ineligible | Narrow margin from one sample; not a reliability bound |
| Cover cleanup | Cancelled terminal reports verified empty keys/buttons | Not per-key release evidence |
| Ammo/progress/terminal | Ammo 40→37 during interval; score 1 kill, no death, no exit | No causal combat-effect or completion claim |
| Current-main source | `session_map01_v15.py` matches; controller, typed observer and V12 owner differ | Historical run used `authored_policy_guard`, not current paired health/ammo fire-cover mode |
| Recovery and useful feedback | Controller received typed HUD health/ammo and canceled the cover | No bounded recovery benefit or independent useful-task-feedback result |

The trace is useful prior evidence that a visible threat/HUD-change sequence can drive this class of health guard to cancel a pending cover before planner completion. Because its controller and input-owner sources differ from the rechecked main head, and because the current main uses paired health/ammo evidence for fire covers, it does not satisfy the fresh current-main test requirement.
