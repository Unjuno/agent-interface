# Saved-history audit v2 for PR #7664

This additive post-hoc repair targets exact source head
`c87812a4a2d41f65127bb3a72fdceea390f63dc7`. It changes no frozen file and does
not execute either historical candidate, runner, experiment, game or input.

## What is independently derived

The auditor reads the retained `followup_raw.json` sample history. It derives
the earliest prior-policy baseline `(105, 0)`, the corrected freshest
post-acceptance/pre-input baseline `(115, 1)`, and the post-input delta
`(130, 0)`. Thus the saved successor rejection follows from the counter values,
not from a hard-coded expected-decision table. The retained decisions and
claimed timestamps are checked only after reduction. Counter values need not
be binary or start at zero.

The accepted timestamp, maximum gap and no-missed-period fixture setting were
not captured independently in the historical raw record. This auditor obtains
them by parsing literal AST nodes in the exact byte-pinned `followup_run.py`.
This is explicitly fixture-specification metadata, not new runtime evidence.
No imported candidate or producer is used as an oracle. Source identity joins
bind both candidate hashes and the prior Git blob to the historical freeze.

## Scope and historical disposition

- The six consumed files must match their exact Git blob and SHA-256 pins.
  `INPUTS.json` also records the eleven unchanged source/evidence files
  downloaded through the GitHub connector for this repair.
- `RESULT.json` is the new saved-record audit output. It does not replace the
  previous audit, raw record, report, freeze or manifests.
- The original seven-case `raw.json` omits events and samples. Its original
  audit remains label/structure-only; this repair does not upgrade it to a
  raw-history audit.
- The historical container gate remains STOP. No actual episode JSONL,
  source-epoch authentication, game event time, physical input, causation,
  useful recovery or MAP01 completion is established.
- This is a bounded one-fixture audit, not a universal scorer implementation.
  The `earliest` reducer option is solely for reconstructing the preserved
  prior-policy defect; `latest` is the default corrected rule.

## Validation

On Linux x86_64, Python 3.12.14, the first red run against the unchanged old
`followup_audit.py` ran 15 methods and had 22 assertion failures including
subcases for its absent independent-reducer API. The unchanged-packet and
wrong-label rejection controls passed. Five separate corrupted history/source
copies were incorrectly accepted: missing history, changed post-input score,
removed pre-input gain, reversed chronology and changed fixture acceptance.
The missing derived-baseline assertion also failed. First-red code and logs
remain in the private repair evidence bundle.

The first repaired run passed 15/15 methods. The final suite passes 17/17 in
normal and optimized Python. Two extra controls locally rebind only the
counterfactual raw-copy identity, then require a derived-decision mismatch for
changed progress or a changed label. Those controls prove semantic comparison
works even when an identity failure does not short-circuit it; the production
pins remain unchanged. The pure reducer controls cover nonzero baselines,
new progress, missing baseline, gap, missed period, malformed values and
nonmonotonic clocks. Compilation passes. All eleven downloaded originals
retain exact Git blob and SHA-256 identity.

Run from the repository root:

```sh
python research/doom/scorer_eventlog_join_t0_v1/saved_record_audit_v2/audit.py
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/saved_record_audit_v2 -p test_audit.py -v
python -O -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/saved_record_audit_v2 -p test_audit.py -v
```

The CLI emits JSON to stdout and never writes historical artifacts. The test
suite copies only the six consumed files to temporary directories. Validation
was confined to this additive saved-data audit; no complete repository suite,
historical producer, formal experiment or original seven-case candidate suite
was run. Existing-PR owner publication, current-main composition, review and
integration remain separate gates.
