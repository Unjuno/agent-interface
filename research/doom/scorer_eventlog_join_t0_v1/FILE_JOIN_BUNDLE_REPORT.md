# MAP01 scorer JSONL run-bundle consumer follow-up

Status: frozen before the candidate test run.

## H / T / D / C / U

**H.** A scorer interval must not be classified from separately selected JSONL files unless all expected runtime artifacts come from one directory and its `sources.json` and `scorer-summary.json` agree with the files and source checkout.

**T.** Run ten deterministic temporary-directory controls from `FILE_JOIN_BUNDLE_FREEZE.json`: one valid bundle, then missing sources, a missing required source, missing summary, altered source digest, unsafe source path, mismatched sample count, mismatched sample-interval summary, mismatched scorer-event summary, and missing scorer-event file. The valid control must preserve the existing bounded admission-bracket result. Every malformed or inconsistent bundle must fail closed before classification.

**D.** PASS only if all seven decisions match the freeze, the valid case reports no causal attribution, and every fault control returns the frozen invalid-bundle decision/reason. Any acceptance of an inconsistent bundle is FAIL; test or source-root ambiguity is HOLD.

**C.** Matching sidecar counts do not cryptographically prove the JSONL bytes were produced by the named runtime. An actor able to rewrite all files and sidecars can create a self-consistent bundle. This check tests accidental cross-run selection, missing/mismatched provenance, and internal summary inconsistency; it does not authenticate hostile artifacts or prove live task effect.

**U.** Synthetic fixtures do not establish scorer cadence under load, exact physical input effect time, causal recovery benefit, or MAP01 progress. The live #59 allocation remains unassigned and outside this test.

## Frozen inputs and scope

- Current `main`: `8e807cd4c4ecd07f53c98f4d1629fbbe3528ac2b`.
- Stack parent: open draft PR #7664 head `c0d7f484e2223e3e6bcae7963b21a682e6efbcc1`.
- Required source closure is frozen in `FILE_JOIN_BUNDLE_FREEZE.json`; those seven source files were identical by Git blob at the stack parent and frozen current `main`.
- Consumer must take one `--run-dir` and resolve `events.jsonl`, `scorer-samples.jsonl`, `scorer-events.jsonl`, `scorer-summary.json`, and `sources.json` only within it.
- Source hashes are checked against an explicit checkout's `research/` root; unsafe paths, missing dependencies, unknown/malformed hashes, and mismatches fail closed.
- No game, model, operating-system input, GPU, container, or live allocation will be used.

## Reproduction

```sh
python research/doom/scorer_eventlog_join_t0_v1/file_join_bundle_run.py
python research/doom/scorer_eventlog_join_t0_v1/file_join_bundle_audit.py
cd research/doom/scorer_eventlog_join_t0_v1
python -m unittest test_file_join_bundle -v
```

The nine controls copy the exact seven required source files from the frozen current-main tree (`8e807cd4c4ecd07f53c98f4d1629fbbe3528ac2b`) into a temporary source root and use their SHA-256 values in `sources.json`. This is a deterministic consumer-integrity construction check only. Even a PASS cannot be promoted to an authoritative live-run audit without a producer-side immutable run manifest binding the JSONL byte hashes at closeout.
