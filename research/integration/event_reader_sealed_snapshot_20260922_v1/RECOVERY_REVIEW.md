# Recovery review: Issue #3979 sealed-snapshot allocation

The old branch contains only `FREEZE.json`. It binds 15 source/environment
files and a 42-case, three-batch formal allocation, but the bound payloads,
formal manifest, raw journals, audit, and corruption outputs are not in the
branch or current `main`. A bounded search of accessible `/tmp` and Codex
workspace paths found no matching local output package.

## Issue-reported formal outcome

Issue [#3979](https://github.com/Unjuno/agent-interface/issues/3979),
comment [5766630789](https://github.com/Unjuno/agent-interface/issues/3979#issuecomment-5766630789),
reports three once-only 14-case batches with actual external exit 0,
42 cases/45 snapshot rounds, and
`PASS_SEALED_SNAPSHOT_IMMUTABILITY_BOUNDARY_SCOPED`. It reports 27 accepted
and 18 refused rounds; full-seal mutation refusal in 12 cases; six mutable
control mutations; three `F_SEAL_WRITE` EBUSY prepublication stops; and three
accepted pre-seal misbindings explicitly classified
`FAIL_PROVENANCE_NOT_ESTABLISHED` for source authentication. The Issue reports
a 675-file formal manifest SHA-256
`0b3fb5b801e3d966edb55fa68dda2d922402627efe4f48620d31e8ba1e92bc7d`, audit
JSON SHA-256
`eb874e35ee1a8d59b5fa78a611b698018133338ba3c79d281d1c89359aac504f`, and an
original corruption report with a known unsorted-batch-loop limitation; a
separate sorted rehash checker is also reported.

None of those result artifacts or their bound source files is available here.
The result counts, hashes, and audit decisions are therefore preserved as
Issue-reported, not independently recomputed from saved bytes. The scoped
immutability PASS does not establish source provenance, production adoption,
ACK, model consumption, durability, or cross-platform behavior.

## Recovery boundary

`FREEZE.json` is retained byte-for-byte. No memfd, process, batch, formal run,
retry, or GUI/model/input action was executed during recovery. Do not rerun the
consumed allocation to recreate missing outputs. Any later-recovered evidence
should be audited from its original bytes without changing this historical
freeze or its reported provenance limitation.
