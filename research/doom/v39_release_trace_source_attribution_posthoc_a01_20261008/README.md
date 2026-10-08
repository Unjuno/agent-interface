# V39 retained release-trace source attribution posthoc A01

## H / T / D / C / U

**H.** The retained MAP01 coast-liveness run has no per-key release timing rows because its recorded source bundle used the V12 base path and did not record the V15 measurement overlay. Its source manifest also contains a mixed set of historical and frozen-tree files.

**T.** Reconstruct all 20 source entries from the retained `sources.json`; hash each against the run manifest and frozen evidence commit; recover the three nonmatching files from their historical Git source; inspect the recorded V12 → V1 → V10 import chain; and count per-key fields in the retained owner release rows. Do not run the game, model, GUI, or input path.

**D.** PASS only when every source-bundle byte matches its retained SHA-256, all entries are attributed either to the frozen evidence tree or the named historical source, V15-only sources are absent from the retained manifest, the V12/V1/V10 import chain is present, and an independent reconstruction exactly matches the complete result. Result mutations and source-byte mutations must fail the audit.

**C.** This establishes what the retained source manifest and owner rows contain. The manifest does not include the top-level launcher source or invocation arguments, so the selected CLI flag itself is not proven. The inferred V12-base/no-V15-overlay explanation is a source-attribution result, not proof of runtime behavior beyond those retained artifacts.

**U.** This posthoc analysis does not establish per-key physical key state, application consumption, useful feedback, recovery efficacy, live threat response, or MAP01 completion. The fresh live threat experiment remains outstanding and separately gated.

## Result

The run manifest lists 20 source files. Seventeen hashes match evidence commit `6149fc1856ce86de41b168de8ca12690347f524d`; three identify exact historical source files from `d5fb50e11f35b52c3d2a861b73dd8f12c2b4b7cf`: `session_map01_v12.py`, `executor_v12.py`, and `doom_typed_observation_v1.py`.

The retained manifest includes the V12 session, typed-release backend V1, and input owner V10. The V12 session imports V1, and V1 imports V10. The manifest does not list the V15 session, release backend V2, transition owner V4, or input owner V12. The retained `owner-events.json` contains 13 owner-release rows and zero rows with either `key_release_attempts` or `key_release_intervals_ns`; the recorded V10 source contains neither field. This supports an instrumentation-path explanation for the absent timing data. It does not prove the exact launcher argv because that source and argv are absent from the frozen run record.

`RESULT.json` is the deterministic candidate reduction. `AUDIT.json` is the independent full-result reconstruction. Six tests pass in normal and optimized Python, including altered-result, unknown-field, mutated-source, and output-overwrite rejection controls.

## Reproduce

From the repository root, use fresh output paths:

```sh
python -B research/doom/v39_release_trace_source_attribution_posthoc_a01_20261008/candidate.py --output /tmp/v39-source-attribution-result.json
python -B research/doom/v39_release_trace_source_attribution_posthoc_a01_20261008/audit.py --result /tmp/v39-source-attribution-result.json --output /tmp/v39-source-attribution-audit.json
python -B -m unittest discover -s research/doom/v39_release_trace_source_attribution_posthoc_a01_20261008/tests -v
python -O -B -m unittest discover -s research/doom/v39_release_trace_source_attribution_posthoc_a01_20261008/tests -v
```

Compare the two generated JSON files with checked-in `RESULT.json` and `AUDIT.json`. Inputs preserve the exact retained source manifest, owner-event rows, and all 20 source snapshots. No live runtime, game, model, GUI, OS input, container, or GPU was used.
