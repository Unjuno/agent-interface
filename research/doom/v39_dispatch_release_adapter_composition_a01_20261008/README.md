# V39 dispatch → V15 release → feedback-attribution composition A01

## H / T / D / C / U

**H.** The vendored dispatch check and release-adapter check compose into one valid measurement route: `--measurement-session` selects V15; the exact V15 source-manifest merger records every per-key release dependency; exact release publication rows join the frozen scorer-feedback adapter; missing publication fails closed, while accepted-but-ambiguous publication remains row-scoped and noncausal.

**T.** Freeze the latest main observed at `e678e9e0b7ffbc949ee5670637519d0af48288ac` and the exact production source blobs listed in `FREEZE.json`. Execute the V39 command helper and V15 `_merge_sources` from source snapshots, then compose the release producer and adapter for complete, before-accept-failure, and after-accept-failure batches. Run once normally and once with `python -O`. Do not start a session, game, model, GUI, container, or OS input path.

**D.** PASS only if both modes select V15 and its exact report label; the V15 source manifest contains all 12 production source entries and the four per-key release dependencies with exact source hashes; complete rows yield `SOURCE_ROWS_JOINED / TEMPORALLY_UNIQUE / NOT_ESTABLISHED`; before-accept failure yields one visible row and `HOLD_INCOMPLETE_RELEASE_BATCH / UNRESOLVED`; after-accept failure yields two ordered observed rows and remains `TEMPORALLY_UNIQUE / NOT_ESTABLISHED`; and normal/-O outputs match byte-for-byte. The independent auditor must reject route, manifest, missing-row, and causal-overclaim mutations.

**C.** This is deterministic source-bound composition of candidate work proposed in #8524 (dispatch) and #8519 (release publisher/adapter). The exact runner, component freeze files, adapter, and scorer-feedback source are vendored and hash-pinned under `candidate_inputs/`, so the experiment does not require either PR to merge or their files to exist in the checkout. Production code remains unchanged. The command and manifest helper run against a frozen source snapshot; release records use the publisher methods with synthetic owner/scorer/sink fixtures.

**U.** It does not launch the selected V15 session, observe physical key state, measure useful-feedback latency, test game/model behavior, establish causal action effect, execute recovery, respond to a live threat, or complete MAP01. The private live lane remains unassigned. This result is only a construction-integrity prerequisite for the separately gated current-main live test.

## Result

The selected command is `session_map01_v15.py` with report label `v15_scorer_only_per_key_release`; default V12 dispatch remains covered by the source-pinned component result from #8524. The exact V15 merger emitted a 12-entry manifest containing the batch release backend, typed release backend, transition owner V4, and InputOwner V12 per-key fields. The composed baseline attributed only the observed row set and explicitly did not establish causality. A sink failure before row 2 was accepted left one row and failed closed. An exception after row 2 was stored left both ordered rows visible but retained `causal_attribution=NOT_ESTABLISHED`.

The original `official-a01` result is retained as historical evidence. Review found its package omitted the open-PR candidate inputs needed for a clean-checkout replay. The corrected, self-contained `official-a02` run was executed against main `e678e9e0b7ffbc949ee5670637519d0af48288ac`; all 13 frozen production blob IDs matched. On the later PR refresh, current main `4a38cb226fd465bbf6b600b1e2f9aa20564f8e01` was checked and those same 13 blobs still matched. A02 exits 0 in normal and `python -O` modes and matches byte-for-byte for both result and source manifest. Its first independent audit receipt (`AUDIT.json`, 9/9) remains preserved. A candidate-input provenance mutation found that the recorded input identity was not independently checked against `FREEZE.json`; the repaired auditor receipt (`AUDIT-recheck-02.json`) passes 10/10. Seven mutation and vendored-input tests pass in both modes (14 test executions total).

The run is source-composition evidence only. It does not turn a successful software receipt into a physical release guarantee or task-effect result. The raw manifest preserves native Windows backslash keys; the independent check canonicalizes only separators before comparing paths, while preserving every manifest byte for hashing.

## Reproduce

From this directory, use fresh output directories:

```powershell
python -B run_modes.py --out-dir outputs/another-unique-name
python -B audit.py --out-dir outputs/another-unique-name/normal --output outputs/another-unique-name/AUDIT-recheck.json
python -B -m unittest discover -s tests -v
python -O -B -m unittest discover -s tests -v
```

`run_modes.py` refuses an existing destination and saves commands, stdout, stderr, exit codes, candidate results, source manifests, and exact source snapshots. The audit writes only to a fresh path. Existing output directories must not be reused. `candidate_inputs/` contains every non-main component file required by the run, so #8519/#8524 do not need to merge for reproduction. The checkout must contain the pinned production source history; candidate inputs are checked from vendored bytes before use.

## Development failures retained

The original harness-development failures are documented in `DEVELOPMENT_FAILURES.md`: a stale local source, an omitted `_sha` helper, a Windows path-separator mismatch, and the A01 packaging omission. A01 raw results remain preserved. A02 is the first self-contained replay and the reproducible package result; none of these harness issues is treated as a scientific outcome.
