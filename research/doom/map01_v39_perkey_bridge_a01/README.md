# v39 per-key release bridge — construction A01

This bounded construction checks whether the current typed backend event adapter can carry the existing InputOwner v12 per-key down/up measurements through a program-step context. It uses the repository's fake X display and XTest harness. It performs no OS input, GUI capture, ViZDoom, model call, Docker operation, or live allocation.

## H/T/D/C/U

- **H:** With the v12 owner substituted at the typed-backend input seam, one admitted F8 down/up pair can preserve a common `intent_token`, `actuation_id`, program/step identity, and a measured physical-up interval in the emitted event stream without granting input authority.
- **T:** Run one fresh fake-display owner and invoke the backend adapter once for down and once for up. Run the independent auditor over the retained event rows. No retries; a setup or semantic mismatch is retained as STOP/FAIL.
- **D:** PASS only if the v12 owner classifies both edges as confirmed, the same actuation identity links down/up, the up interval is ordered, the backend labels both rows with the same program/step/token, fake key state and backend hold state are empty after up, and all authority flags remain false.
- **C:** This may only prove test-harness composition. It does not establish that the production v39 startup closure loads this adapter, that a live X server emits the same observations, that the application consumes a key event, or that the path improves threat response or recovery.
- **U:** No GUI, game, real keyboard, model, task effect, or latency benefit is measured. The fake X server reports its own controlled keymap transitions; timing values are local `perf_counter_ns` brackets around fake-display calls.

## Reproduction

From `research/doom`, run the unit suite; then return to the repository root for the frozen one-shot candidate and independent audit:

```sh
cd research/doom
python3 -B -m unittest -v map01_v39_perkey_bridge_a01.test_bridge
cd ../..
python3 research/doom/map01_v39_perkey_bridge_a01/run_construction.py
python3 research/doom/map01_v39_perkey_bridge_a01/audit.py
```

The runner creates a unique `results/construction-a01/` directory and refuses to overwrite it. `candidate-events.jsonl` is the retained raw stream. The per-key edge is nested under `physical_key_measurement.adapter_edge`; it is not a top-level `input_release_transition`, so current v39 consumers still need an explicit schema adapter before relying on it. The audit independently checks the raw event identity, edges, and authority boundary against `FREEZE.json`. The consumed A01 output must remain intact; any new construction execution needs a new run ID and output path.

The next live v39 allocation still needs a fresh exact source closure, current allocation ownership, GUI/input resource checks, and its own preregistered stop rule. This result does not authorize or substitute for that allocation.
