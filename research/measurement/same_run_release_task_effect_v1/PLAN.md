# #4134 H/T/D/C/U freeze

H: one private X11 session can retain a post-XSync plan/actuation/key-bound `key_released` receipt and an independently journal-bound TASK_EFFECT on one monotonic clock without promoting release, callbacks, background state or terminal neutrality to task success.

T: PRESS_EFFECT / RELEASE_EFFECT / STATE_ONLY / BACKGROUND_EFFECT, 3 repetitions = 12 fresh sessions; private Xvfb/Tk/XTEST; separate scorer; no model/MAP01. Construction-01/02 failures and construction-03 eligibility are excluded.

D: exact 12 sessions; one valid release receipt each; 3 press + 3 release TASK_EFFECT; 3 state + 3 background unresolved; lineage/clock/authority/terminal-neutral gates; raw audit errors=[]; >=8 coherent mutations rejected.

C: same-host X-server measurement, not physical HID; single actuation only; no general causal attribution.

U: no MAP01 usefulness/recovery efficacy/model/token/human-tempo/cross-platform/production claim.

Formal command after public source/hash readback: `python -B run_matrix.py --out formal-01 --reps 3 --display-base 620` exactly once.
