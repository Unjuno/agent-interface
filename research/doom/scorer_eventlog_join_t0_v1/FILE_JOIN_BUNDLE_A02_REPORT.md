# MAP01 scorer JSONL run-bundle consumer follow-up A02

Status: preregistered against current main and current #7664 stack source before this version's candidate run.

## H / T / D / C / U

**H.** A scorer interval must not be classified from separately selected JSONL files unless all runtime artifacts are read from one directory and the source closure and scorer summary match the exact frozen source tree.

**T.** Execute the ten controls in `FILE_JOIN_BUNDLE_A02_FREEZE.json`: one valid joined interval plus missing sources, missing required source, missing summary, changed source hash, unsafe source path, wrong sample count, wrong interval summary, wrong event summary, and missing scorer-event file. Run focused tests and an independent auditor that compares every required Git blob against both frozen main and the stack parent.

**D.** PASS only if all ten expected decisions match, the valid case remains explicitly noncausal, every malformed bundle rejects before classification, all 11 bundle tests pass, and the audit confirms both source trees and raw hashes. Any source-tree mismatch is HOLD; any inconsistent bundle accepted is FAIL.

**C.** Sidecar reconciliation and source hashes catch accidental file mixing, stale source selection, missing dependencies, and summary inconsistency. They do not authenticate artifacts if an actor can rewrite all episode files and sidecars together; an authoritative live-run audit still needs a producer-side immutable manifest binding JSONL byte hashes at closeout.

**U.** Fixtures are synthetic. They do not establish scorer cadence under load, exact physical input effect time, causal recovery benefit, or MAP01 progress. The separate live #59 allocation remains unassigned.

## Frozen source identity

- Current main: `52d2c7a7b6f4854d9d9de43d001a1d8ebfbfaacf`.
- Current #7664 stack parent: `cf8200378e4e895da2c6b492a4b6f307b56aee56`.
- Both trees contain the seven exact same Git blobs and SHA-256 file contents listed in `FILE_JOIN_BUNDLE_A02_FREEZE.json`.
- `file_join_bundle_a02_audit.py` rechecks the frozen Git objects and checked-out source files before it accepts the raw JSON.
- The consumer takes one `--run-dir` and reads `events.jsonl`, `scorer-samples.jsonl`, `scorer-events.jsonl`, `scorer-summary.json`, and `sources.json` only from that directory. It checks source path confinement and hashes, sample/event schemas and isolation, sample timing summaries, and scorer event/count summaries.
- No game, model, operating-system input, GPU, container, or live allocation was used.

## Reproduction

```sh
python research/doom/scorer_eventlog_join_t0_v1/file_join_bundle_a02_run.py
python research/doom/scorer_eventlog_join_t0_v1/file_join_bundle_a02_audit.py
python research/doom/scorer_eventlog_join_t0_v1/file_join_bundle_a02_audit_v2.py
cd research/doom/scorer_eventlog_join_t0_v1
python -m unittest test_file_join_bundle -v
```

The A01 output remains retained but is not promoted: its correction is in `FILE_JOIN_BUNDLE_A01_DISPOSITION.md`.

## Executed result

`file_join_bundle_a02_run.py` executed all ten frozen controls once. The valid same-directory bundle preserved `ADMISSION_BRACKETED_PROGRESS` with positive sample 130 and `causal_attribution=false`; all nine missing, malformed, stale-source, path, or summary-corruption controls returned `POST_CANCELLATION_COOCCURRENCE / invalid_or_missing_run_bundle`. The independent A02 audit passed with an empty error list after confirming all seven Git blobs and content hashes at both frozen refs.

The complete focused suite passed **18/18** tests (11 run-bundle tests plus 7 existing consumer/policy tests); Python 3.11 compilation and `git diff --check` passed. The tests and runner are local deterministic synthetic construction on Windows. No game, model, OS input, GPU, container, or live allocation ran.

Before publication, main advanced to `c99d93a2c81945f0946173e48247bdd49e32a02a`. All seven required source Git blobs still match the A02 freeze and the stack parent, so the frozen source basis remains valid.

The #7664 stack later advanced by force-push to `a2f85482c6968f9caa9dcbca017bd452b8a2c3b3` and added a seven-case same-directory metadata checker at `runtime_bundle_a01_20261005/`. That adjacent result addresses co-location and summary presence, but states that it does not validate full scorer/event source content. A02's distinct increment is hashing the complete seven-file producer/adapter dependency closure against the checkout and reconciling scheduler/sample intervals plus scorer event summaries. The seven frozen source Git blobs match at the refreshed `c99d93a` main and `a2f8548` stack head. The A02 candidate raw was not rerun; `file_join_bundle_a02_audit_v2.py` independently checks the retained raw against the original freeze and refreshed refs without requiring the force-pushed old stack commit to remain an ancestor.

For the overlap check, the upstream A01 suite at `runtime_bundle_a01_20261005/test_candidate.py` passed 9/9. Its tests exercise the stated metadata/source-policy and sample-count gate; A02 adds checks for actual source-file bytes and internal scorer event and timing summaries. The results remain separate and are not pooled. The older sibling `file_join_bundle_a01_test.py` refers to an earlier `FILE_JOIN_BUNDLE_FREEZE.json`; its source-equality setup fails against the current checked-out producer bytes, so that legacy test was not counted as the upstream A01 suite or as A02 evidence.

After the upstream stack update, main advanced to `18bf390d0c230b5a2ee9675cebffbc0e51bfea2d`. The v2 audit was rerun against that current main and stack `a2f85482c6968f9caa9dcbca017bd452b8a2c3b3`: all ten retained raw rows remain valid, the audit returned zero errors, and all seven required producer/adapter Git blobs still match across the frozen refs, refreshed refs, and checked-out sources. This was a saved-result/source audit only; the ten-case candidate runner was not rerun. Current direction remains r134 and the live #59 evidence gate remains unresolved.

Disposition: **PASS, scoped to source-bound run-bundle consumer construction.** This closes the declared missing-sidecar/source-check for this consumer only. It does not make existing or future episode outputs self-authenticating; a producer-side immutable manifest of JSONL byte hashes is still needed before any live result is called authoritative. It does not advance the live #59 allocation gate by itself.
