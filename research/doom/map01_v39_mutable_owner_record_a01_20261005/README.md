# V39 mutable owner-record custody A01

This is a candidate-implementation follow-up to merged PR #7832, not a new discovery. PR #7832 reproduced the mutable-record custody failure in a pinned container and retained a diagnostic neutral-state revisit probe. This packet compares a production-shaped bridge candidate: instead of scanning every record at each drain, it retains only unverified record indices and deduplicates per-key rows by `(record_index, row_index)`. The predecessor #7805 A09 bridge/test remains unmodified upstream.

The underlying schedule is: bridge drains a mutable `owner_release` dictionary while aggregate reconciliation is pending. If a per-key sample is unavailable, the partial record has no confirmed-up row; the bridge advances its cursor and retains F8. The owner later updates the *same* dictionary to `verified=true` with empty key/button sets, but a cursor-only second drain misses that update and leaves F8 stale in `Backend.held`.

## H / T / D / C / U

- **H — Hypothesis:** the #7832 diagnostic full-record revisit can be narrowed to a pending-index set while preserving unverified-row semantics and avoiding duplicate publication.
- **T — Test:** reuse the #7832 deterministic barrier schedule and replay the candidate on current main after the #7832 merge.
- **D — Decision:** #7832 already supplies baseline RED and diagnostic GREEN. This candidate PASS requires pending-index revisit to clear `held`, preserve one unconfirmed per-key measurement, leave fake state empty, and pass adjacent #7805 candidate/composition suites in normal and optimized mode.
- **C — Consequence:** use a pending-index set for unverified records and deduplicate rows by record/row index. This is a candidate implementation comparison, not a fresh reproduction or live/runtime fix.
- **U — Unverified:** real X11 timing/frequency, runtime integration, application consumption, useful feedback, safety, live gameplay, and whether the live MAP01 path encounters this schedule.

## Pins and execution

- Current main replay: `ab4c0571c84be727378907618347c56ac8f19d41` (includes merged #7832 and unrelated #7837); earlier current-main snapshots are not the final validation base.
- Prior discovery and container raw: merged [PR #7832](https://github.com/Unjuno/agent-interface/pull/7832), package `research/doom/map01_v39_mutable_release_record_custody_a01_20261005/`.
- Predecessor candidate: PR #7805 head `311f834bf63111b344297f947f8546128c7a1844`; baseline bridge blob `9028c652d2134b3f748b99069069748e1aef2cdf`.
- Predecessor owner candidate blob: `e7889a7a34fe76df5f230d4108a77055b105a680`.
- Current-main dependencies are pinned by Git blob IDs in `SOURCE_LOCK.json`.
- Runtime: host CPython 3.14.5, native macOS; no X server, GUI, game, or OS input.

From repository root:

```sh
python3 -m unittest research.doom.map01_v39_mutable_owner_record_a01_20261005.test_mutable_owner_record -v
python3 -O -m unittest research.doom.map01_v39_mutable_owner_record_a01_20261005.test_mutable_owner_record -v
python3 -m py_compile research/doom/map01_v39_mutable_owner_record_a01_20261005/test_mutable_owner_record.py research/doom/map01_v39_mutable_owner_record_a01_20261005/bridge_v2_candidate.py research/doom/map01_v39_mutable_owner_record_a01_20261005/input_owner_v13_candidate.py
python3 research/doom/map01_v39_mutable_owner_record_a01_20261005/audit.py
```

The preserved predecessor remains unchanged in its own PR. This packet copies its owner candidate into a new path and contains a candidate-only bridge successor; it does not modify runtime or promote the candidate.
