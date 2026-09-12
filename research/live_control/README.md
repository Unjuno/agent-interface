# Asynchronous live control: development evidence

Latest experiment: [observed-focus binding and wrong-target probes](FOCUS.md).
`interactive_v7.py` is experimental; observe-only recovery still needs work.

Latest: [independent input release under blocked logging/capture](INPUT_OWNER.md).
The [interactive owner follow-up](OWNER_SELF_USE.md) adds `interactive_v6.py`
and records actual assistant use, including a retained Calc task failure.

Follow-up: [cooperative intent expiry and input-boundary fault injection](LEASE.md).
Use `session_v4.py` for the current lease experiment; other revisions retain
their original behavior and evidence.

Follow-up: [revision 2 decision boundaries and assistant trial](DECISION_BOUNDARY.md).
The description below records the original `session.py` revision.

This research prototype separates command reading from a single GUI execution
worker. A planner can submit a finite program, receive early acknowledgements
and observations, and request cancellation while the worker is active.
It uses the existing private Xvfb application fixtures and exact O2 transport.
It is not yet a general desktop runtime or a human-speed agent benchmark.

## What is implemented

- Whole-program validation and a private copy before any input; 1–16 steps.
- One active program, explicit identifiers and rejection of implicit queuing.
- Text, key, chord, held keys, public-window-title wait and observation steps.
- Held-key duration up to 5 seconds per step; combined hold/wait budget up to
  10 seconds. These are nominal bounds, not hard deadlines under blocking I/O.
- A separate cancellation reader, per-character/loop cancellation checks,
  key release on every terminal path, and X11 keymap release verification.
- Periodic observations during holds and title waits, exact packet decoding,
  PNG reuse and separate input/observation/terminal timestamps.
- Independent task scoring only after execution ends.

`completed` means the submitted program ended; it does not assert task success.
Title matching uses public X11 window metadata and is not visual-only control.
No idle observation stream, pointer control, focus/stale-state guard, hard
watchdog, disconnect lease or production protocol hardening is implemented.
Only trusted local JSON producers are in scope. Blocking capture, file output
or stdout can delay cancellation; these measurements do not establish a bound.

## Recorded development runs

| Run | Result | Interpretation |
|---|---|---|
| `development-01` | Initial reader failed before task input | An Xlib setup warning polluted stdout; retained source snapshots and events document the failure. Setup diagnostics were then separated from JSON. |
| `development-02` | 6/6 scripted tasks; 54 exact frames | XTerm and Calc, three seeds each. Tests cancellation, input release, invalid-tail/busy rejection and timeout stopping subsequent steps. |
| `development-03` | 6/6 scripted tasks; 54 exact frames | Fresh seeds 820301–820303 after copying accepted programs and rejecting unverified release. Same functional checks pass. |
| `dogfood-01` | Assistant missed cancellation; recovered task succeeds | The five-second hold finished and its trailing text ran before the assistant's cancel arrived. Cancellation reported `matched: false`. The assistant inspected the image, cleared the line with Ctrl+U and submitted the required token; independent output equals `t830101`. |

In `development-03`, server cancellation-request timestamp to verified key
release ranged from **0.50 to 20.79 ms** across six scripted probes. These are
local, uncontrolled development observations, not model response times or a
latency guarantee. See each `probe.json` and `events.jsonl`; source snapshots
and inherited source hashes are retained with the runs.

The actual assistant's missed cancellation is the important counterexample:
the cancel request arrived roughly **176.20 seconds after program completion**,
across a conversation context handoff. This is not a typical-latency estimate.
It shows why a responsive local cancel channel alone cannot ensure timely
planner intervention. The trailing `must-not-run` string was ordinary test
input, not an executor invariant: it ran because no cancellation had arrived.

Next design work should give movement intents an explicit expiry policy and
stop/deoptimize before actions requiring another decision. A normal finite
hold currently ends successfully and continues to the next submitted step.
Do not infer a lease or a semantic guard from its duration field.

## Reproduce

Run under the documented Ubuntu/WSL X11 research environment, from this folder:

```sh
python3 -m unittest test_executor -v
python3 probe.py --out results-local-fresh --seed 840101 --pairs 3
python3 session.py --app xterm --seed 840201 --out results-local-session
```

Choose unused output paths; generated local folders above are examples, not
ignored repository paths. Use the repository's `results-local/` directory for
unpublished work. The interactive process accepts newline-delimited JSON:

```json
{"op":"submit","id":"move-1","steps":[{"op":"hold","keys":["Left"],"duration_ms":1000}]}
{"op":"cancel","id":"move-1"}
{"op":"finish"}
```

Use pipes for machine consumption; the assistant's PTY adds terminal wrapping
to displayed output, while `events.jsonl` retains the original event records.
The ready event supplies the fixture task. `finish` cancels any active program,
then scores the actual application output and closes its private session.

Five executor unit tests and the fresh six-task live probe passed. A separate
unit test mutates the caller's accepted program while execution is paused and
verifies that the originally accepted steps run to completion.
This is a development record, without preregistered efficacy comparisons,
measured model tokens, a comparable human baseline or a DOOM run.
