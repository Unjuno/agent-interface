# Actual disk-prefix recovery after process exit — #6509

Decision: **PASS_PROCESS_EXIT_BOUNDARY_SCOPED** for nine frozen, authored native Windows construction cases. This is a new ordinary construction boundary after the original logical T0; neither historical allocation was rerun.

See [report](REPORT.md), [prospective plan](PLAN.md), [source/case freeze](FREEZE.json), [run commands and UTC exits](RUN.json), [first raw](results/boundary-01/raw.json) and [separate retained-file audit](results/audit-01.json). SHA256SUMS pins the published files. The original [T0](../claim_scoped_partial_verdict_6509_t0_20261002/REPORT.md) remains unchanged.

From repository root, ordinary tests:
```text
python -m unittest discover -s research/analysis/claim_disk_recovery_6509_01a0ff58 -p test_recovery.py -v
```

To inspect retained evidence without rewriting it:
```text
python research/analysis/claim_disk_recovery_6509_01a0ff58/audit.py research/analysis/claim_disk_recovery_6509_01a0ff58/results/boundary-01 NEW-AUDIT.json
```

The audit refuses an existing output. A fresh ordinary construction matrix, if justified, needs a distinct output, identity, freeze and retained first result. Do not overwrite or rerun this boundary-01 to improve its outcome.

All labels describe synthetic check receipts. The package is research-only and neither imports into runtime nor grants GUI/input authority. Process-exit visibility is not power-loss durability, concurrent publication, exactly-once consumer effects or a performance claim.

## Versioned audit correction after independent review

Independent comment 5964379370 on PR #6891 found four copied-raw mutations that audit v1 accepts: a reader beginning before writer exit, child argv/mode disagreement, an unfrozen interpreter string, and a COMPLETE reason attached to a PARTIAL result. The original observations match that reviewer's independent checker. The defect is the automated gate's missing metadata/full-result joins. Original v1 checks must not be read as automatically validating UTC order, argv, frozen environment or every recovery field; those had depended on source/manual inspection.

Original audit.py, FREEZE.json, six source/case identities, all nine journals/markers, raw/RUN/audit/first logs remain byte-identical. Original documentation/manifest are copied under historical/ and identified by original head d6d27e98230f3dd0302a985dfab043126a4c1ff4. No writer/reader/producer or formal allocation is rerun. New audit_v2.py imports neither v1, writer nor reconstructor. It independently derives exact journal/marker bytes and every result field, and checks typed process schemas, literal child argv/case joins, frozen environment, and serial chronology bounded by original FREEZE/RUN. Recorded UTC is wall-clock metadata and is not independent proof of causality under clock adjustments or malicious forgery.

The pre-repair v2 delegate to unchanged v1 produced nine expected assertion failures across six test methods; source/log are retained. The four review controls and ten additional type/coverage/provenance controls now reject. Original retained data still yields 3 complete / 1 counterexample / 5 unknown, 15 completed checks and two false cached completions. FREEZE-v2.json is an ordinary post-discovery audit-source/input freeze, written after local repair tests and before the first standalone v2 raw audit; it is not an experimental pre-registration or replacement for the original source freeze. RUN-v2.json records actual audit/test UTC, argv, exits and output hashes. See AUDIT-v2.md. No stronger process, durability, semantic truth, external effect, authority or performance claim is added.
