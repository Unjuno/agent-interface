# V16 source-epoch identifiability probe A01

- **H:** V16 can attach the current wrapper run/update ID to scorer values returned by a stale prior-episode cache because the `ProgressSample` callback carries no source epoch.
- **T:** Compare exact current-main `AcknowledgedSampler` and `ProgressClockV2` in two deterministic histories: one samples live counters; the other returns cached prior-epoch counters after a valid client update while current game state differs.
- **D:** A counterexample is established if reported samples, client-update sidecars, and progress events are byte-equivalent while underlying current state differs.
- **C:** The stale-value callback emits a current sample clock after the successful update acknowledgment, matching the wrapper timestamp contract. `run_id` and `update_sequence` therefore prove the wrapper update, not the callback's data origin.
- **U:** Synthetic source-level identifiability only. This does not show that the real engine returns stale values or establish a runtime freshness failure.

The runner pins current-main commit `5c52cc4c08e96312338228ae5a566c2436eabc37` and checks source Git blobs before importing them. The original harness indexing failure and initial test-import STOP are retained; no candidate test ran on either failed attempt. The corrected runner saves complete compared samples, sidecar rows, and events in `result.json`; `audit.py` independently checks the recorded values and file hashes.

Validation on the same frozen current-main commit:

- V16 acknowledged-sampler and finalization regression suites: 15/15 passed.
- Probe: fresh and stale histories emitted identical samples, update rows and `KILL_COUNT_INCREASE` events although their current kill counts were 2 and 3.
- Independent artifact audit and `py_compile`: passed.

Run from repository root:

```powershell
$env:PYTHONPATH='research/doom'
python research/doom/v16_source_epoch_identifiability_59_4d74_20261004/probe.py
python research/doom/v16_source_epoch_identifiability_59_4d74_20261004/audit.py
```

This is a source-level synthetic counterexample. It does not demonstrate an actual engine cache failure or qualify runtime freshness or gameplay.
