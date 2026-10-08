# Explicit return to the planner, revision 2

The first assistant trial demonstrated that a responsive cancel channel does
not help when the planner's request arrives after a finite program finishes.
Revision 2 introduces `decide`: publish an observation, terminate with
`needs_decision`, verify input release and discard the program tail. There is
no implicit resume; the planner submits a new program.

Each submission requires `expected_sequence`, equal to the latest emitted
observation sequence. This rejects outdated references before input, but does
not prove the screen is unchanged since observation. Idle capture, focus guards,
age limits and atomic observation/input are absent. This is not an execution
lease or a hard deadline. Programs without `decide` retain sequential behavior.

```json
{"op":"submit","id":"bounded","expected_sequence":1,"steps":[{"op":"hold","keys":["Control_L"],"duration_ms":500},{"op":"decide"},{"op":"text","text":"must-not-run"}]}
```

Start `session_v2.py` with the same arguments as `session.py`. After the terminal
event, inspect its preceding observation and submit a new identifier using that
sequence. Existing v1 source and evidence are unchanged. New source hashes are
recorded in the trial's `sources.json`.

## Actual assistant use

`results/decision-dogfood-01`, XTerm seed 850101:

- The assistant inspected the initial screen and submitted the program above.
- `needs_decision` verified release; the trailing text step never started.
  The boundary observation reused the initial blank screen image.
- An intentionally outdated sequence 1 request was rejected before input.
- A fresh sequence 9 request typed the token, pressed Return and waited for
  the public saved title. Independent file scoring confirmed `t850101`.
- The fresh request arrived **10.998 seconds** after the boundary terminal.
  The tail remained unexecuted. This is one assistant/tool interval, not a
  representative latency estimate or a controlled speedup comparison.
- An offline audit reconstructed all **12 frames** exactly and checked PNGs.
  Two unit tests cover tail discarding, fresh continuation and invalid/old
  observation references.

```sh
python3 -m unittest test_executor_v2 -v
python3 audit_decision.py results/decision-dogfood-01
```

## Next experiment and related work

Stopping at every boundary would preserve seconds-scale planner stalls. The
objective remains overlapping useful execution with planning, requiring another
decision where the next action's meaning is unknown. Compare boundary placement
and bounded local continuation under measured planner delays on a dynamic task;
measure waiting, correctness and task time together.

Primary research consulted on 2026-09-13:

- [Real-Time Execution of Action Chunking Flow Policies](https://arxiv.org/abs/2506.07339)
  studies asynchronous execution to address latency and discontinuities between
  action chunks in robotic flow policies.
- [Real-Time Robot Execution with Masked Action Chunking](https://arxiv.org/abs/2601.20130)
  identifies mismatch between executed chunks and current perception as a
  failure mechanism during asynchronous robot inference.

Our inference is to measure temporal alignment as well as transport speed.
These robotic-policy results do not prove GUI performance or validate our
boundary implementation. No token reduction, human comparison, continuous
visual tracking or DOOM result is claimed here.
