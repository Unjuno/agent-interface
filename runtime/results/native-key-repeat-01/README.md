# Explicit key repetition through the existing guarded native batch

Related idea: [#2867](https://github.com/Unjuno/agent-interface/issues/2867).
Disposition: **PASS_NATIVE_REPEAT_SCOPED** for exact compilation, bounded refusal
and one primary-assistant live use. Model-token/latency utility remains unmeasured.
This does not implement or complete the broader persistent queue proposal.

The primary assistant previously wrote 18 repeated Right operations. The guarded
native bridge now accepts `{"op":"key_chord","keys":["Right"],"repeat":18}`
in its existing tail. Compilation removes `repeat` and produces independent,
ordinary key_chord operations. No new runtime opcode, target authority, implicit
wait, input retry or asynchronous execution is introduced. This means repeated
press/release pairs, not an autorepeating held key.

Counts must be integers 1..126 (booleans/floats/strings rejected). Only key_chord
can carry repeat. Expanded tails must fit 123 operations for click or 126 for
keyboard, leaving room for the existing wrapper within the core's 128-op bound.
The entire tail expands before guard capture/admission; overflow is not truncated
or split into another program. Each copy has independent nested values. Existing
core validation, target checks, lease, release and recovery refusal remain.

After 40 local tail/bridge/exchange tests passed, source hashes were frozen. The
primary assistant started one fresh seed 991105 Inkscape allocation, viewed the
initial rectangle, chose its edge at (600,378), and submitted a leading 50 ms
wait, repeat 18 Right, another 50 ms wait and Ctrl+S. The returned image showed
x=86. Explicit finish returned successful directional task scoring and completed
cleanup; independent SVG parsing also verifies x=86/y=50/width=40/height=30.
There was no correction or replay. Owner handle 54327 separately exited 0.

The compact decision is **249 bytes versus 849 bytes** for the semantically
identical flat decision using the same sorted, compact JSON encoding: 600 bytes
or 70.7% less in this request. Images, responses, context and actual model token
usage are outside that comparison. The dispatched program still has 26 ops and
43 input emissions; execution work is not reduced. This is one use, not a
matched model-quality or latency experiment.

`audit.py` independently constructs the expected flat operation list, checks the
actual program against it and against the retained prior flat request, rejects
corrupted count/order/row-count examples, verifies pre-use source hashes, request
digests, 16 image references, output geometry, release and cleanup. The audit
does not call the compiler being assessed and never replays input. Source base
8576c0fd1d43aec861d0d7c9761c1a3bbc545caf; changed sources are under `source/`.
The prior flat request comes from `native-key-boundary-01/primary/request-1.json`.

Commands:
```sh
PYTHONPATH=.:research/live_control python3 -m unittest \
  research/live_control/test_native_tail_v1.py \
  research/live_control/test_native_handle_bridge_v1.py \
  research/live_control/test_native_exchange_v1.py
python3 runtime/results/native-key-repeat-01/audit.py
```

No sensor work, helper model or Docker restart was performed. Nested loops,
scheduled actions, queue cancellation and application-level readiness remain
outside this syntax extension. Existing frozen failures remain unchanged.
