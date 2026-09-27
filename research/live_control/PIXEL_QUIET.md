# Bounded pixel-quiet observation: first assistant trial

`interactive_v9.py` adds an explicit `settle` step through `session_v8.py`.
It samples full reconstructed frames and input-focus IDs until successive
samples are equal for the requested quiet interval, or the observation budget
expires. It never labels this as semantic completion. All intermediate frames
and events remain archived and are currently also emitted to the client.

```json
{"op":"settle","quiet_ms":80,"timeout_ms":750}
```

Validation accepts quiet intervals of 40–250 ms and timeouts from the quiet
interval to 2,000 ms; combined explicit hold/wait budgets remain at most ten
seconds. The intent deadline and cancellation still apply. Input focus is bound
once per program, even if initially unknown. Settling cannot authorize an input
tail whose original focus binding was unknown or invalidated.

The interval uses times after snapshot processing returns. It therefore includes
capture, codec, artifact and synchronous logging overhead. It only measures
equality at sampled points, not continuous visual inactivity. Capture or logging
can overrun the timeout, and a final quiet result can be recognized after the
nominal budget. This is cooperative observation, not hard real-time scheduling.

## Actual assistant use

In `quiet-assistant-01`, the assistant inspected Calc and issued cell entry,
Ctrl+S and a settle step in one program. The final image showed the fully painted
Excel-format dialog. The assistant then issued Return plus settle, inspected the
worksheet and finished. Independent saved-workbook evaluation confirmed
A1=368 and A2=773.

The dialog settle used three samples and 165.118 ms; the post-confirmation settle
used five samples and 342.362 ms. Both reported `pixel_quiet`. Fifteen packet
frames match archived PNG pixels, both programs verified input release, and
owner shutdown verified release. No separate observe-only program was required.

The preceding recovery trial used four programs and nine frames; this trial used
two programs and fifteen frames. They used different seeds and occurred in a
learning sequence, so these counts do **not** establish a causal reduction,
general speedup or token savings. The local work and emitted observation volume
increased. A matched planner comparison and compact delivery integration are
still needed. First-image-ready timing also differs from the final quiet image.

## Counterexamples and validation

Six tests passed. They cover restarting the interval on pixel changes, clearing
it on ambiguous focus, continuous change timing out, cancellation before capture,
and preventing a settle step from granting authority to an unknown input tail.
One explicitly retained counterexample shows that a static **loading screen**
also satisfies quietness. A blinking caret or ongoing animation can conversely
prevent quietness even when the UI is usable. Quietness must not become a hidden
task-success gate or a default wait before every game action.

Run from this directory in the documented Ubuntu/WSL environment:

```sh
python3 -m unittest test_quiet_window test_settle -v
python3 audit_owner_sessions.py results/quiet-assistant-01
python3 interactive_v9.py --app calc --seed 950201 --out ../../results-local/quiet-new
```

The session manifest freezes the new and inherited runtime sources. This is one
exploratory self-use trial. Next: compare matched task runs, record final useful
feedback and planner-boundary timings, and reduce presentation volume while
retaining intermediate focus/critical-event evidence. Generic readiness,
human-speed interaction and real token savings remain unproven.
