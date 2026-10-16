# Live binding-resolved framed pointer intents v1

The resolution-transfer studies initially required the runner to calculate new
absolute coordinates. This candidate moves that calculation into Agent Interface
admission. A planner supplies source coordinates together with an explicit
`screen_chrome` or `window_content` frame and the geometry on which those
coordinates were authored.

`executor_v4` deep-copies the complete program, asks `session_v26` to resolve all
frame-bearing operations against the latest stable `pointer_binding`, validates
the resulting raw program, emits auditable `coordinate_frame_resolved` records
and only then starts execution. The supported candidate operations are:

- `pointer_click_in_frame`;
- `pointer_drag_in_frame`;
- `local_target_guard_postcondition_in_frame`.

The condition's target and guard boxes use the same frame transform as its
related pointer path. Resolution grants no authority. Existing InputOwner checks
still require the observed focus, surface, geometry and point hit to match before
each pointer input.

One preregistered fresh OpenTTD pair runs at1152x720 while the runner sends only
the original1024x720 coordinates. The runtime reads target geometry
`[65,40,1152,720]`, keeps screen chrome at `[0,0]`, and resolves map paths and
boxes by `[-64,0]`. The completed-segment repeat returns
`target_not_reached`, suppresses the continuation and independently remains
false. The target returns `met`, executes the continuation and independently
completes the five-tile L. Actual X11 pointer-admission records contain resolved
map points and do not contain the original first point. Both cases use six
durable calls; all69 frames replay exactly on Windows and WSL.

A second preregistered live fault changes the client geometry after whole-program
resolution and before the first pointer operation. Resolution records
`[65,40,1152,720]`; the test-only X11 move produces
`[82,60,1152,720]`. The following click reaches `step_started`, but the existing
InputOwner geometry check returns `needs_decision` with zero pointer-admission
records. The move-to-terminal interval is28.435ms and submit-to-terminal return
is105.333ms. Input release is verified, the save remains unchanged and the
independent task score is false.

This proves scoped live transformation and a tested post-admission geometry
refusal. It does not prove automatic frame selection, semantic identity under
internal scrolling or camera movement, general race freedom, model performance
or improved speed. Positive/repeat drag-to-condition remains2.482/2.573 seconds.

Decision: retain `executor_v4`, `session_v26` and the explicit-frame operations
as research candidates. Next remove the task-specific frame declaration from the
runner by binding points to named observed regions or affordances, and test a new
save or internal viewport movement. Keep raw absolute pointer operations as the
universal fallback until broader evidence exists.
