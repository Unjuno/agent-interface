# V15 scorer/input attribution adapter construction T2

## H / T / D / C / U

- **H:** Current-main V15 scorer and input-release producer rows can be normalized into the frozen #7537 gate without timestamp-proximity joins, and incomplete telemetry cannot receive a unique intent label.
- **T:** Exercise the real `ScorerFileSink` and `ProgressClock` writers with a two-sample counter transition. Feed six source-shaped per-key input traces into `adapter.py`; compare one exact same-intent interval, competing intents, mismatched identity, unverified release, incomplete batch publication, and missing admission identity. Run the independent raw-result audit and the frozen T0 tests.
- **D:** `PASS_V15_PRODUCER_COMPOSITION_SCOPED`. The verified full-span single intent is `TEMPORALLY_UNIQUE`; competing overlapping intents are `AMBIGUOUS`; all four incomplete/mismatched cases are `UNRESOLVED` or HOLD. Every result retains `causal_attribution: NOT_ESTABLISHED`. The candidate ran once, audit ran once, and 18 tests passed.
- **C:** T2 is a producer-composition construction. Scorer samples/events are produced by the current `ScorerFileSink` and `ProgressClock`; the per-key input rows are complete source-shaped fixtures, not output from X11 or a live DOOM session. The T1 retained v39 trace is older and lacks these scorer and identity-bound release records.
- **U:** No scorer accuracy/usefulness, real-session publication completeness, task effect, causation, safety, recovery benefit, survival, human tempo, or MAP01 result is established. No game/model/GUI/OS input or live allocation ran.

## Adapter contract

`adapter.py` accepts V15 scorer sample envelopes, independent progress event rows, and runtime input rows. It rejects controller-visible or mismatched scorer schemas. Admissions and key-up rows must join on exact owner, intent token, program id, step, and key. A verified release requires a matching owner-explicit-keyup XSync receipt, the backend's verified transition flags, and a complete release batch whose positions exactly cover `0..size-1`. Missing admissions or orphan releases cause a global HOLD; unverified key-up remains a possible overlap and cannot complete coverage.

The partial-batch adversary exposed an actual defect during construction: with `release_batch_size=2` but only one reported row, the first adapter version returned `TEMPORALLY_UNIQUE`. The failing test is retained in `red-batch.*`; validating batch membership now returns `HOLD_INCOMPLETE_RELEASE_BATCH` and `UNRESOLVED`.

## Validation and evidence

```powershell
python -B -m unittest -v test_adapter.py test_t0.py test_runner.py
python -B run_t2.py --run-dir run/replay
python -B audit_t2.py --run-dir run/replay
```

The runner requires an output path that does not already exist and refuses to append to or overwrite an existing run. The commands above write a replay under `run/replay/`; choose a different fresh path for another run. The retained T2 evidence under [`run/`](run/) remains immutable. The T2 gate source and V15 scorer producer files are pinned in `FREEZE.json`. The real scorer writer emits two samples and one positive kill-count event per replay. The fixture timestamps 100 and 300 ns and its 35 Hz summary field are synthetic inputs, not an observed sampling interval or rate. The source-shaped actuator rows and six outcomes are saved in the selected run directory. The independent raw-only check for the retained original run is [`AUDIT.json`](AUDIT.json).
