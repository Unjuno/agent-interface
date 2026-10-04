# V39 mutable owner-record custody A01

This additive successor isolates one bookkeeping race not covered by the open PR #7805 A09 suite. The bridge drains a mutable `owner_release` dictionary while aggregate reconciliation is pending. If a per-key sample is unavailable, the partial record has no confirmed-up row; the bridge advances its cursor and retains F8. The owner later updates the *same* dictionary to `verified=true` with empty key/button sets, but a cursor-only second drain misses that update and leaves F8 stale in `Backend.held`.

## H / T / D / C / U

- **H — Hypothesis:** mutable owner-release records can cross the consumer while unverified and later become verified-empty without another list append; a cursor-only bridge then cannot reconcile its local held ledger.
- **T — Test:** admit F8; force the per-key post sample unavailable; stop owner cleanup at a deterministic `query_pointer` barrier after the partial record append; drain once; release the barrier; drain again after the same object is updated.
- **D — Decision:** baseline must demonstrate `held={F8}` after verified-empty update (RED). Candidate PASS requires the repeated drain to clear `held`, preserve exactly one unconfirmed per-key measurement, and leave fake physical state empty. Normal and optimized (`-O`) runs must agree.
- **C — Consequence:** retain unverified record indices for reconciliation until they become verified-empty, and deduplicate already published rows by record/row index. This is fake-display candidate mechanics only.
- **U — Unverified:** real X11 timing/frequency, runtime integration, application consumption, useful feedback, safety, live gameplay, and whether the live MAP01 path encounters this schedule.

## Pins and execution

- Current main: `0015aea71eeef36ed53513ace5a952dc9cb265c6`.
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
