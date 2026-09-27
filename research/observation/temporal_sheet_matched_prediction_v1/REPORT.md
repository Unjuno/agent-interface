# #1565 model-free matched-presentation construction

Decision: **`PASS_TEMPORAL_SHEET_MATCHED_PRESENTATION_CONSTRUCTION`**.

Six deterministic motion histories were generated in a disposable container using a standard-library RGB renderer and PNG encoder. No model/provider/GUI/X11/task input was used.

## Main construction result

- scenarios: **6**;
- source frame geometry: **320x250 RGB**;
- four-frame source pixel count: **320,000**;
- packed geometry: **640x500 RGB**;
- packed pixel count: **320,000**;
- equal separate/packed pixel budget: **6/6**;
- packed quadrant raw-RGB hashes exactly equal the four source-frame raw hashes: **6/6**;
- CURRENT_ONLY PNG hash equals source frame4 PNG hash: **6/6**;
- history roles exact `[historical,historical,historical,current]`: **6/6**;
- historical/current samples grant no input authority;
- independently generated oracle values remain outside model-visible prompt/pixels.

Primary audit: PASS/errors[]; corruption controls **6/6** reject source-ID, source-hash, history-role, pixel-budget, order and prompt mutations.

Independent audit: PASS/errors[]; exact quadrant cases6/6, equal pixel budget6/6.

## Frozen scenarios

`steady_right`, `steady_left`, `stationary`, `recent_reversal`, `history_then_stop`, `moving_target_static_decoy`.

Several histories end at the same current target coordinate, making CURRENT_ONLY intentionally unable to recover the distinct prior direction. This supplies a history-value discriminator while the separate-vs-packed comparison isolates presentation.

## Scope

This is mechanics evidence only. It establishes that a future model comparison can hold source pixels and total history-arm pixel count exactly fixed while changing only image segmentation/layout. It does not show that packed sheets improve prediction, tokens or latency.

The frozen next allocation is 18 prediction-only calls (6 scenarios x3 arms), fresh independent session per call, requested `gpt-5.6-luna` / low effort, with no task input. A separate explicit model allocation is required before execution.

## Local identities before publication

- fixture.py SHA-256 `92407123a2243cd6fdfeda4a8f26cd192bab3d56d1b00cff7b7384bfdaa88c56`
- audit.py `491644743adfa9fa2c7d327bacb3ddadfb3e78040ca41de25bafafe8f3a2917b`
- independent_audit.py `3688d13fec07064b5c9104bd7963a0f5210b16acb3296c225535598d9ccbe718`
- MANIFEST.json `0928c1939812e6bbc8c28487e19d941b651d697f4e7cdb8ffad75b6d4c0ae0d0`
- AUDIT.json `df7c77e4862040b6b460617929491a7dfc2344e9734222e4630360b1f4660ba1`
- INDEPENDENT_AUDIT.json `a902acb9385aa0416d0c895025a09c2ef8be4c4e8c63934b2cf99722a6ceb993`
