# Soft-observation stale-submit boundary — A01 result

Disposition: `PASS_SYNTHETIC_SOFT_REJECTION_RECOVERY`.

The frozen regression first failed against PR #7904's pre-repair controller: sequence 7 was submitted, sequence 8 arrived, the fake validity monitor classified it as soft (no invalidation), and the id-less stale-sequence rejection escaped `submit_cover()` as `RuntimeError`. The controller did not record a decision from the fresh observation.

The repair returns a rejected response only for the initial cover submission. The initial gate records the response as `status=rejected`, captures the latest observation as the decision source, records no admitted cover, skips cancellation/release handling because no program was admitted, skips the planner turn, and advances the controller loop. Renewal submissions retain their previous fail-closed behavior; this change does not define renewal recovery.

Validation on the combined PR branch:

- `python -m unittest research.doom.test_overlap_controller_v39_wait -v` — 13 passed.
- `python -O -m unittest research.doom.test_overlap_controller_v39_wait -v` — 13 passed.
- `python -m unittest research.doom.test_map01_overlap_controller_v39 -v` — 6 passed.
- `python -O -m unittest research.doom.test_map01_overlap_controller_v39 -v` — 6 passed.
- `python -m unittest discover -s research/doom -p test_source_refresh_v1.py -v` — 13 passed.
- `python -O -m unittest discover -s research/doom -p test_source_refresh_v1.py -v` — 13 passed.
- `python -m py_compile research/doom/map01_overlap_controller_v39.py research/doom/test_overlap_controller_v39_wait.py` — passed.
- `git diff --check` — passed.

The initial attempt to invoke the source-refresh test as a module failed because its sibling import requires the `research/doom` discovery path. The corrected discovery command above passed; this was a test-command setup error, not a source failure. Raw RED and verification outputs are retained in this directory. `audit.py` checks the source snapshots and test-output dispositions without rerunning the candidate.

This demonstrates a bounded synthetic controller recovery path, not that soft observations occur at any particular rate or that this change improves live control. No game, model, GUI, X server, OS input, or live allocation was used. It does not establish physical release, useful feedback, recovery efficacy, task effect, survival, or MAP01 completion. Issue #59 remains open and the private live-game allocation remains unassigned.
