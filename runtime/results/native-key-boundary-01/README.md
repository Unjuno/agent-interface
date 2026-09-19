# Click-to-key boundary: fixed ABBA check and primary-assistant use

This follows the x=84 observation after 18 Right chords retained in
`native-terminal-cleanup-01`. It uses the existing native exchange and unchanged
Inkscape 1.2.2 on WSL/X11. No new input API, default delay, sensor or helper model.

Before execution, `study/PLAN.json` fixed four sequential fresh private
allocations with seed 991105, point (600,378), 18 Right chords, 50 ms before Save,
and post-click delays 0/50/50/0 ms. Each initial target patch had to match the
primary-assistant's previously viewed source exactly. The script used the actual
harness/exchange, recorded each raw reply and finished without correction.
These four runs are program checks, not four model-directed trials.

| Run | Post-click wait ms | Saved SVG x | Program ms | Existing task score |
|---|---:|---:|---:|---|
| 1 | 0 | 84 | 264.601 | pass |
| 2 | 50 | 86 | 328.044 | pass |
| 3 | 50 | 86 | 303.751 | pass |
| 4 | 0 | 84 | 282.565 | pass |

For the secondary motor-count check, 18 default two-unit nudges from x=50
predict x=86. Both no-wait runs fell short; both 50 ms runs matched. This small
ABBA result supports a click-to-key timing hypothesis under this configuration.
It does not locate the lost/coalesced/ignored input event or establish an optimal
delay, general reliability, causal mechanism, speed or model-token improvement.
All programs completed with 43 emissions and verified neutral release; dispatch
completion did not establish exact displacement. Fresh process timing differs.

Crucially, the existing evaluator deliberately checks **rightward movement and
preserved y/size**, not exact motor gain. All four task passes are valid under
that contract. `goal.dx` is the fixture's nominal drag distance in screen pixels,
not a demanded SVG-coordinate displacement for keyboard use. Earlier narratives
calling x=86 the task's exact goal conflated these two checks. Frozen evidence
and scores are unchanged. The harness now exposes the existing task contract,
SVG coordinate frame, tolerance and dx meaning before action.

The primary assistant then used a fresh allocation with that public task, viewed
the initial image, chose the same edge point with an explicit leading 50 ms
`wait_update`, sent 18 Right chords and Save, viewed x=86 and finished. The saved
SVG is x=86/y=50/width=40/height=30, with no transform. No correction was needed.
The final reply includes completed cleanup; its owner handle 70695 exited 0.
The four-study owner exited 0 (handle 88497), and each child exit is recorded.

Caller recipe: for this measured click-then-key case, place
`{"op":"wait_update","timeout_ms":50}` at the beginning of the click tail.
It delays input, **not** acknowledges application readiness. Keep reviewing the
returned image and saved effect. Keyboard-only continuation is a different case;
the policy is not automatically injected there or into every application.

X.Org describes XTEST as server-side simulated input and server event delivery
to clients. A server synchronization round trip does not establish the app's
semantic result. See [XTEST reference](https://www.x.org/releases/X11R7.5/doc/man/man3/XTestFakeKeyEvent.3.html)
and [input event processing](https://www.x.org/Development/Documentation/InputEventProcessing/).
Current upstream Inkscape source includes event coalescing, but it is not the
pinned installed version and is not used as proof of this run's cause.

Source base: 9d35b04f0bc5d3ffa7d4c34ca6697eb695b58ce2. `source/pre-change-harness.py`
is the exact base blob used for the four study runs. The primary used the changed
task-description harness snapshot. Audit verifies raw action order, image hashes,
request/reply digests, preserved output geometry and cleanup; it never replays
input. Run `python3 runtime/results/native-key-boundary-01/audit.py`.
