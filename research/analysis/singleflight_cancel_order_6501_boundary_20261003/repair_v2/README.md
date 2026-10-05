# Typed retained-data audit repair v2

The frozen v1 auditor accepted six effective corruptions of copied raw JSON: Boolean row ids, floating point event time/rank, a foreign caller, and an undeclared row field. `first-characterization.json` records the original errors=[], source/data hashes and all six exact copied-data hashes. `controls/` preserves those copies losslessly. This is a substantive audit correction over retained evidence, not a rerun of the consumed formal allocation.

`auditor_v2.py` reconstructs the finite event-prefix oracle independently using only the standard library. Recursive equality requires exact JSON scalar types, closed object keys and ordered arrays. It checks all 192 Cartesian assignments and 384 waiter decisions. The unchanged raw passes with 48 incorrect admissions for the strict timestamp rule, 48 incorrect refusals for the conservative timestamp rule and zero discrepancies for explicit order. Invalid-row counters are reference calculations and must not be treated as validated observations.

The corrected portable test has seven methods. All fourteen serialized-effective controls reject, including the eight legacy controls and six saved false accepts. `execution-verified/` contains actual child exits, UTC timestamps, stdout and audit output: tests exit0 and retained-data CLI exit0. `FREEZE-VERIFICATION.json` binds corrected source/fixtures before that ordinary verification; it does not claim preregistration of a new formal experiment. `verify_retained.py` provides a portable read-only custody and control check.

The first portable custody wrapper then failed because it used `SHA256SUMS` instead of the parent's actual `PACKAGE-SHA256SUMS` filename. Its exit1 and path-sanitized first traceback are preserved separately; after correcting that filename, `portable-fixed.txt` and its receipt record exit0. This did not change the auditor, raw or the already passing seven unit methods.

An ordinary packaging failure (`base64` was not imported) initially left `controls/` empty. The first portable test/readback loops consequently examined zero saved files, although the separately generated fourteen controls were exercised. The original `execution/` logs are retained and qualified by `PACKAGING-REPAIR.json`; the corrected saved-file checks require six fixtures. `PROVENANCE-CORRECTION.json` and `execution/test_auditor_v2.initial.py.txt` distinguish the first portable test from the earlier work-only test. No first log or formal raw has been replaced.

All twenty files from publication v3 remain byte-identical, including the old auditor, README, report, freeze, raw projection, first result and original nineteen-entry manifest. Read this repair together with those historical records: the old audit is an observed result with six demonstrated detection gaps. `SHA256SUMS` here binds only this new repair directory, excluding itself. Public command receipts replace local path strings with placeholders; source/data/stdout bytes and timing/exit fields are retained. Earlier public Git history remains accessible.

From this directory, using Python 3.12 or compatible standard library:

```text
python -B -m unittest -v test_auditor_v2
python -B verify_retained.py
```

For the CLI, recover `../run01/candidate-raw.json.gz.b64` using base64 followed by gzip into a fresh private output path, then run `auditor_v2.py <raw-path> --expected-raw-sha256 60759e1b49d03a7d83bb3968b892c2c349f7e89842f17aa645043785421a580b --output <fresh-audit-path>`. Never run the parent `run_once.py` again against its consumed allocation.

Scope remains a two-waiter finite analytical delivery model. This proves neither real asyncio/OS scheduling, shared runtime suitability, GUI task effects, authentic logs against coordinated fabrication nor strict duplicate-member JSON parsing. No shared runtime, workflow, discovery configuration, original candidate, original construction test or main ref is changed by this repair.
