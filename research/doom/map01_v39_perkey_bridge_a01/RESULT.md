# Construction A01 result

**Disposition: PASS_CONSTRUCTION.** One fresh fake-display construction produced the expected per-key up receipt; the independent raw-event auditor returned zero errors. This does not qualify a live v39 run.

The retained v39 control trace is pinned to main `4ca1db66b6adcb4ea15fc3c744315ad39a87749e`: 634 events, SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`, one aggregate `input_released` row, and zero `input_release_transition` or `input_release_measurement` rows. `results/construction-a01/baseline-check.json` independently inventories those event names and source hash.

Construction A01 ran once on macOS with Python 3.12.14. The current typed backend raw adapter was paired with the actual frozen InputOwner v12 code running its existing fake X display/XTest harness. The adapter emitted two rows: one confirmed down and one confirmed up. Both rows carried `cover-7`, step `2`, and `intent-v39-a01`; the v12 actuation ID matched across both edges. The up receipt carried an ordered per-key physical-up interval, and its authority flag was false. Fake physical state and backend hold state were empty afterward.

The candidate raw stream is `results/construction-a01/candidate-events.jsonl`, SHA-256 `ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e`. Its per-key edge is nested in the measurement payload; it does not yet match the top-level event name used by the historical v39 observability analyzer. The independent audit is `results/construction-a01/audit.json`, status `PASS_CONSTRUCTION`, errors `[]`. The runner’s source-path preflight STOP is retained separately at `results/preflight-stop-01/STOP.json`; it occurred before candidate invocation and was not overwritten.

## Scope limits

The capture superclass was not instantiated; its image/X11 import graph was isolated because only the raw-event adapter was under test. The fake display does not establish that production v39 startup loads this bridge, that an actual X server emits the same samples, that the application consumes the key, or that the telemetry improves threat response, recovery, survival, completion, time, or token cost. No GUI, OS input, ViZDoom, model, Docker, or shared allocation was used.

The result supports carrying v12 per-key identity and timing through this adapter boundary. A future live allocation still needs a full fresh v39 source closure, matched threat exposure, independent useful-feedback and recovery measurements, and current ownership/resource gates. It does not authorize the held F03 formal launch or any other allocation.
