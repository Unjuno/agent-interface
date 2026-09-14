# MAP01 visual-stagnation candidates

The retained 30-decision reflex failure repeatedly returned to close wall and
door views. A conservative local detector downsamples the visible game viewport
to 64x45 grayscale and reports a revisit only when a non-adjacent view from the
previous eight decisions has normalized mean absolute error at or below 0.065.
The calibration is frozen on that one failed run. It reproduces eleven selected
revisits, but it is not a general wall, position, or progress classifier.

Three ordered allocations then used the same `gpt-5.6-luna` low-effort model,
normal Freedoom 2 MAP01, skill 1, seed 990606, 40-decision limit, four-turn model
session span, semantic motor compiler, X11 input backend, and continuously
advancing 35-tic game. The initial candidate forced an escalating recovery
program for every detected revisit. The baseline retained the prior controller.
The final candidate exposed a structured advisory only after at least three
revisits in five decisions and never overrode the model command.

| Allocation | Exit | Deaths | Kills | Revisits | Wall s | Model s | Input tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| forced recovery | no | 0 | 1 | 10 | 379.604 | 298.985 | 394,040 |
| baseline | no | 0 | 2 | 5 | 363.290 | 304.767 | 394,339 |
| planner advisory | no | 0 | 2 | 18 | 376.634 | 313.247 | 400,904 |

Six of ten forced recoveries left the matched visual cluster by the next
decision, but the run still accumulated twice as many revisits as the baseline.
The advisory fired twelve times. Five corresponding model assessments explicitly
acknowledged a revisit, and the model selected lateral movement, retreat, or a
different door attempt. It nevertheless remained near a striped door and ended
with eighteen detected revisits. Both candidates changed behavior without
improving completion, so neither is promoted.

This result narrows the next interface layer. A repeated-view directive does not
say which component of a motor program failed. The next candidate should capture
after individual semantic commands and return local effect receipts such as
`no_visible_forward_motion`, `turn_changed_view`, or `use_had_no_visible_effect`.
Those receipts must remain visual observations rather than claims about hidden
position or door state. Their capture overhead, added round trips, prompt tokens,
and gameplay effect need direct measurement.

[The command-effect receipt study](MAP01_EFFECT_RECEIPT_V1.md) performs that
measurement. Existing in-hold samples provide first visual feedback around
45--47 ms after command issue with zero added executor steps. Compact no-effect
projection changed the planner's immediate action, but a 40-decision matched
pair still failed to exit MAP01 and did not reduce revisits. The next measured
gap is the 8,682.54 ms median from no-effect observation to the next admitted
model plan.

The work also exposed two clean-start dependencies. `session_map01_v5.py`
implicitly relied on an external `PYTHONPATH` to locate `gui_suite`, and the first
controller invocation used the WSL system Python rather than the pinned ViZDoom
environment. `session_map01_v6.py` makes the repository module path explicit;
`map01-session-v6-smoke-01` verifies startup, X11 focus/pointer binding, and a
71-tic advance over 2.030 seconds using ViZDoom 1.3.0. The empty controller
startup failure is retained locally. The controller now reports an exited child
and its stderr immediately instead of ending later with `_queue.Empty`.

Run the repository-backed audits with:

```sh
python research/doom/audit_map01_stagnation_v1.py
python research/doom/audit_map01_stagnation_live_v1.py
```

Full high-frequency runtime streams remain in `results-local/doom`. The committed
record includes every decision source frame, model action and token receipt,
environment/scorer output, contact sheets, exact candidate sources, and hashes.
