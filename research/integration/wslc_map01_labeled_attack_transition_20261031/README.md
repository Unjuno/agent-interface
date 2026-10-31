# MAP01 labeled attack-transition pilot (2026-10-31)

This is one fresh, fixed-protocol WSLc allocation, extending the [labeled camera-shift pilot](../wslc_map01_labeled_frame_tracking_20261031/). It asks whether two unchanged offline pixel candidates continue to return a point after a visible target changes state. This is a benchmark case, not a live authorization mechanism.

Freedoom2 MAP01 skill 1, seed 991031, was navigated with guarded X11 inputs. After five frames, a single guarded F-key attack requested a 1,000 ms hold; fifteen more frames followed. The game reported its kill count rising from 0 to 1 across the attack. In the recorded same-state engine labels, object 14 is `Zombieman` in frames 0–4 and `DeadZombieman` in frames 5–19. This association and counter change are observations from the same simulator, not an independent external ground truth.

Both unchanged methods returned the initial oracle-provided point inside the target box on the first five frames and abstained on all fifteen subsequent frames. The benchmark does not distinguish which visual change caused abstention. All three guarded actions reported verified neutral releases; the final owner close also reported a verified release and the recorded keymap contained none of the tested keys.

`aa04.zip` retains the predeclared conditions, runner, unchanged scorer, 20 hashed RGB frames and labels, action receipts, full result and container log. Run `python audit.py` with Python, Pillow and NumPy to verify hashes, releases, labels, and offline rescoring. The source container image and runtime are identified in `conditions.json`; network was disabled. No model was called.

The 20 frames are correlated samples of **one** trajectory. Engine-provided frames and labels are not the live X11 screenshot contract, and the initial target location is supplied by the label oracle. This does not establish general identity tracking, false-positive rate, safe attack authority, post-recovery control, efficiency against a model baseline, or MAP01 completion. Other failures such as occlusion and identity changes still require separate counterexamples.
