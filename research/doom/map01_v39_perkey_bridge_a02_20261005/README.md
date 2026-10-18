# V39 per-key bridge — V4/V12 construction A02

This construction executes the retained `doom_retained_input_backend_v4.Backend.execute/raw` methods with the retained V12 transition adapter and its fake X display. Two distinct fake keycodes exercise one two-key release batch. It records each synthetic keymap sample and input edge, then independently audits the emitted per-key measurements and V4 post-batch receipt.

## H/T/D/C/U

- **H:** V4's correlated release batch can carry V12's per-key confirmed up edges for two controls, while keeping the existing post-batch verification and false-authority boundary.
- **T:** Run one two-key press/reverse-order release sequence on a fresh fake V12 owner. Retain emitted events and an operation trace; run the raw-only audit afterward. The test fixture assigns distinct keycodes because its default mapping collapses all keys to one code.
- **D:** `PASS_COMPOSITION_DIAGNOSTIC` requires two matched confirmed down/up edges, ordered per-key intervals, V4 batch verification, empty final physical/backend state, false authority flags, and the observed operation trace.
- **C:** The V4 capture superclass is stubbed by the existing component test fixture. This exercises V4's actual `execute/raw` methods and the actual V12 owner/adapter over fake display calls; it does not exercise production session startup or capture.
- **U:** Fake query and call intervals are diagnostic observations, not a hard latency bound. No live X server, GUI, OS input, game, model, application effect, threat-response result, or recovery efficacy is measured.

## Reproduction

From `research/doom`, run the focused construction test. From the repository root, run the frozen candidate once and then the independent audit:

```sh
cd research/doom
python3 -B -m unittest -v map01_v39_perkey_bridge_a02_20261005.test_v4_composition
cd ../..
python3 research/doom/map01_v39_perkey_bridge_a02_20261005/run_construction.py
python3 research/doom/map01_v39_perkey_bridge_a02_20261005/audit.py
```

The one-shot output is `results/construction-a02/`; the runner refuses to replace an existing result. `operation-trace.jsonl` reveals V12's two keymap queries between the two release edges. The audited call gap is retained for this fake-display run only; it does not establish a latency distribution or hard bound. A live V39 study still needs its own current source closure, assigned resource ownership, and preregistered response/recovery gates.
