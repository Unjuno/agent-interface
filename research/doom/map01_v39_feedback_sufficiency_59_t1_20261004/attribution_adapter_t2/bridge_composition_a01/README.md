# v39 physical-key bridge to scorer attribution: construction A03

## H / T / D / C / U

**H:** The V15 attribution adapter can consume the merged v39 bridge's nested per-key physical down/up measurements and identify one intent only when the scorer detection bracket lies within the interval known to be held.

**T:** Reuse the exact two-row v39 bridge output from main commit `3eca051c4f561a72a29566aaefcea2923071263a`. Generate scorer samples with the frozen `ProgressClock` at deterministic times inside the bridge's guaranteed-held interval, then pass the rows through the adapter. Exercise mismatched actuation ID, unconfirmed up, and missing up controls. No engine, OS input, game, or model runs.

**D:** PASS scoped if the adapter emits one verified per-key interval and `TEMPORALLY_UNIQUE` for the fully covered scorer bracket, while all three controls remain unresolved and causal attribution stays `NOT_ESTABLISHED`.

**C:** The bridge event stream comes from the retained fake X display construction, not a live session. Scorer timestamps and kill-count transition are deterministic synthetic fixtures chosen inside the edge uncertainty bounds. The result checks schema composition and conservative interval handling only.

**U:** No scorer accuracy/usefulness, live event publication, keymap identity, application consumption, task effect, threat response, recovery efficacy, safety, survival, human tempo, or MAP01 completion is established. This does not satisfy #59's live allocation gate.

## Result

A03 passed. The bridged down/up rows share the exact owner, intent token, program ID, step, key, and actuation ID. For the positive test, the scorer bracket `[87811364895916, 87811364921124]` lies within the definitely-held interval `[87811364895916, 87811364946333]`, using the latest possible physical down and earliest possible physical up. The adapter returns one `TEMPORALLY_UNIQUE` intent envelope, leaves causality unestablished, and marks no input authority. Mismatched actuation, unconfirmed up, and missing up each remain `UNRESOLVED`.

A01 and A02 are retained STOP outcomes: both reached output persistence but produced no candidate files. Their STOP records remain alongside A03. A03's independent audit is `PASS_SCOPED_BRIDGE_COMPOSITION`.

## Reproduction

From `attribution_adapter_t2/`:

```sh
python -B -m unittest -v test_bridge_composition.py
python -B bridge_composition_a01/run_composition.py
python -B bridge_composition_a01/audit.py
python -B -m unittest -v test_adapter.py test_t0.py
```

The runner refuses to overwrite its result directory. All times are local monotonic-style fixture values from the frozen bridge stream; the scorer transition is synthetic and is not a live observation.
