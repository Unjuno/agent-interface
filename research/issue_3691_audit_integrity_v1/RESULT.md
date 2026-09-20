# Issue #3691 — audit integrity successor result

Date: 2026-09-21 Asia/Tokyo

## Decision

- Native construction: `PASS` (7/7 tests; Python 3.11.9).
- Local Docker validation: `STOP_DOCKER_ENGINE_UNAVAILABLE`.
- Overall Issue gate: incomplete; do not treat native tests as the required container result.

## Findings reproduced against merged main

The exact merged auditor source was fetched from GitHub. Four individually constructed mutations were accepted with `PASS_OFFLINE_STRUCTURAL_AUDIT` and `errors=[]`:

1. changed both fixture pixel digests, replaced the supplied freeze, and updated raw.freeze_sha256 to the replacement freeze digest, while the study FREEZE still recorded the predecessor raw/freeze hashes;
2. `final_emissions: true`;
3. `click.emissions: true`;
4. `effect.count: true`.

The replacement freeze digest was `f63d5d090bbc6c98ee37c9e7a0a0c154672b739647d1690efac3750a155858b1`. Exact #3675 raw and predecessor freeze digests remained `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807` and `f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe`. The old artifacts were not modified.

## Remediation construction

The additive auditor compares the bytes of raw/FREEZE with the predecessor hashes in its study manifest, uses exact Python types for booleans/integers, validates positive identity integers and hash shape, and rejects duplicate JSON keys. The local suite passed:

```text
test_duplicate_json_keys_are_rejected (test_integrity.AuditIntegrityTests.test_duplicate_json_keys_are_rejected) ... ok
test_exact_raw_freeze_and_direct_cli_routes_agree (test_integrity.AuditIntegrityTests.test_exact_raw_freeze_and_direct_cli_routes_agree) ... ok
test_json_boolean_never_satisfies_integer_count (test_integrity.AuditIntegrityTests.test_json_boolean_never_satisfies_integer_count) ... ok
test_original_and_successor_event_mutations_are_rejected (test_integrity.AuditIntegrityTests.test_original_and_successor_event_mutations_are_rejected) ... ok
test_pristine_fixture_schema_is_accepted (test_integrity.AuditIntegrityTests.test_pristine_fixture_schema_is_accepted) ... ok
test_replacement_raw_and_freeze_are_rejected_by_manifest_binding (test_integrity.AuditIntegrityTests.test_replacement_raw_and_freeze_are_rejected_by_manifest_binding) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.090s

OK
```

Source SHA-256: audit.py `4c959fb83a4e7523ce50c5f33152b58bd5381776282ecbc6cd53447c1ef23ee9`; test_integrity.py `de5733a0a9ba60a8e23cfed9be406f229249db71d1f1a9b2198910f43d494c9f`. The retained raw and predecessor freeze hashes are listed above.

## Docker stop

A local Docker invocation failed before container creation with a Docker Desktop content-store I/O error on a referenced SHA-256 blob. Follow-up diagnostics found the `desktop-linux` engine pipe absent and `com.docker.service` in Manual/Stopped state. Starting Docker Desktop as the current user did not restore the engine; starting the service was denied because the service could not be opened. No image pull, storage modification, or container execution occurred. This is a bounded infrastructure STOP, not a test FAIL or PASS.

Docker gate still required: run the exact suite once in a network-disabled container with read-only source, then invoke the auditor in a second fresh container after the engine/image store is healthy.

## Construction QA trail

The first CLI attempt was correctly fail-closed with `source hash mismatch: audit.py`: the study manifest contained a one-character transcription error in the source digest. After correcting the manifest to the independently measured source SHA-256, the same CLI command was rerun against the unchanged predecessor inputs and passed. This is recorded as a construction-manifest QA failure followed by a corrected native construction PASS; it is not Docker validation.

The retained CLI output is `artifacts/native_audit.json`, SHA-256 `36e1e9c64c83be35eef3447d76d78d2f62adff257612184beef4162c5e1fb32a`. It reports `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`, and all 11 listed corruption controls rejected.


A later mutation-control refinement changed the auditor source so the replacement-raw self-check now hashes a concrete JSON fixture with both pixel digests altered. The frozen digest was refreshed only after this edit. The immediate stale-freeze CLI attempt correctly stopped with a source-hash mismatch; after updating the manifest, the unchanged-fixture CLI again passed with all 11 controls true. The latest six-test transcript remains in `artifacts/native_tests.txt`; the CLI JSON is unchanged and retains SHA-256 `36e1e9c64c83be35eef3447d76d78d2f62adff257612184beef4162c5e1fb32a`.


## Fail-closed malformed-input regression

The final native suite also supplies a JSON array as the raw root and as the study-manifest root. Both return `FAIL_AUDIT` with errors instead of leaking an exception. The final suite is 7/7 tests; final source digests are recorded in the updated `FREEZE.json`.
