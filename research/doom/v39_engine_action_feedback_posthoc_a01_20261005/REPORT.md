# Result — MAP01 engine-action feedback posthoc A01

**Disposition: `HOLD_OFFSET_FEEDBACK_CENSORED`.** The independent raw audit passes integrity, but the retained scorer window does not contain a post-release sample for one pulse.

The analysis covers all six cells of the already-consumed `absolute_pair_59_4d74_20261004` sample-pair-02 result: three coast controls and three pulse cells. It reads the frozen runtime event stream, scorer last-action samples, and cell result for each. Twenty-four input files are pinned in `FREEZE.json` by commit, Git blob ID, byte count, and SHA-256.

All six `d` admissions join uniquely to a verified owner-thread `KeyRelease`/`XSync` receipt with the same intent token, program, and step. In every pulse, a coherent scorer call reports `Button.MOVE_RIGHT` while the admitted hold is still active. The first positive scorer-call observation brackets fall 6.239–31.978 ms after `admitted_ns`; this is an observation delay, not an exact game-action transition time. Five holds later have a neutral sample 14.999978–45.586281 ms after `release_call_returned_ns`.

For `02-pulse`, step 2, the last scorer sample reports `MOVE_RIGHT` and returns 1.019 ms before key-up returns. The six-second scorer window ends 11.060 ms after key-up returns, and it contains no scorer sample after key-up. Neutral-after-release feedback is therefore right-censored by the sampler. This does not show that the game continued moving after release.

All three coast cells have no admission/release events and no `MOVE_RIGHT` sample. Every cell's retained post-control score is zero kills and no MAP01 exit. The pulse action reached the game’s sampled action state, but there is no scored task effect, useful feedback, recovery outcome, or MAP01 success in this result.

The original run is not repeated. No game, model, GUI, OS input, or container was started for this posthoc reconstruction. The analyzer and independent auditor run on local CPU and the five mutation tests pass.

## Reproduction

From the repository root:

```powershell
python research/doom/v39_engine_action_feedback_posthoc_a01_20261005/analyze.py
python research/doom/v39_engine_action_feedback_posthoc_a01_20261005/audit.py
python -m unittest discover -s research/doom/v39_engine_action_feedback_posthoc_a01_20261005 -v
```

`analyze.py` and `audit.py` retrieve only hash-pinned blobs with `git cat-file`. The tests reject an unverified key-up, a missing in-hold action sample, a fabricated neutral timestamp for the censored pair, and a modified action-onset boundary.

## Decision for the next authorized measurement

Keep scorer collection alive beyond each verified key-up until a neutral action sample arrives or a prospectively fixed finite post-release limit expires. Record the sample call brackets and the independent task scorer separately. Then measure task effect onset and bounded recovery under matched conditions; this result alone does not authorize that live allocation.
