# One-shot execution record — A01

- Allocation: `GUI-REVERSIBILITY-7949-JOURNAL-A01-20261007`.
- Intake main: `2d227ecf86479cff093123190560bd8d63148ce4`.
- Freeze commit: `ead09fb8fda2d5579078211b4fc3fabe4435227`.
- Freeze manifest: `FREEZE_SHA256SUMS.txt`; all 11 entries verified before formal execution and the frozen sources were not edited afterward.
- Platform/runtime: macOS 27.0.1 arm64; `/opt/homebrew/opt/python@3.14/bin/python3.14`, Python 3.14.5 (Clang 21.0.0.123.102).
- Container gate: `docker info` exit 0 (OrbStack CLI 29.5.2 / Engine 29.4.0; linux/aarch64; kernel `7.0.5-orbstack-00330-ge3df4e19b0a0-dirty`). Read-only `docker image ls --no-trunc` failed because existing content blob `sha256:6274b31351429a9cd2385f76c75c2df9f817c3dca6d285f4cd8ccceb88d8d1ad` returned `operation not supported`. `docker ps -a` showed 100 stopped, 0 running. No container or image was changed; no repair, restart, prune, pull, or build. Preregistered native fallback used; no container-isolation claim.
- Pre-freeze construction only: `python3 construction_test.py` PASS; `python3 -m py_compile writer.py observer.py run_all.py candidate.py auditor.py invoke_stage.py construction_test.py` exit 0. Formal DB/stage CLIs were not invoked in construction.

## Formal invocation counts and exits

1. `python3 run_all.py` — exit 0; six new DBs; six writer subprocesses exit 0 and six read-only observer subprocesses exit 0 (12/12 process exits). Exact commands, stdout/stderr and timestamps are in `out/process_receipts.json` and individual `out/process/*.json` receipts. No retries.
2. `python3 invoke_stage.py candidate` — wrapper exit 0; candidate subprocess exit 0, stdout 30 bytes, stderr 0 bytes. One invocation.
3. `python3 invoke_stage.py auditor` — wrapper exit 0; auditor subprocess exit 0, stdout 147 bytes, stderr 0 bytes. One invocation.

Candidate: six decisions, no input errors. Auditor: `PASS_JOURNAL_STATE_RECONCILIATION_SCOPED`, six DB reconstructions, zero errors, output mutation controls 4/4 rejected, raw mutation controls 4/4 rejected, authority/external actions 0. See `POST_RUN_QUALIFICATION.md` for the non-idempotent-restoration gap.

## Retained outputs

- `out/observations.json` SHA-256 `491f2884c0fb2c078c5f14b82618a5b7737b4febf7d40b92cf371d4861bf3488`.
- `out/candidate.json` SHA-256 `f250f482f146901d97bd29bc1943022e048f5b0e082e35c7ee8c366233bf2e8d`.
- `out/audit.json` SHA-256 `390db527c214e967693bf56ea7300df5a134d0463ad8993c479ea34efd8fd782`.
- `out/process_receipts.json` SHA-256 `39c4b846c00b4331a69a91783f87d762736dd0a04faee97962641b7d38168e67`.
- SQLite DB SHA-256s: baseline `cfc0ab2058fcb8b754dbf874a1929ea4c3ffdb17aab7a4713cb18143872552d2`; complete_disjoint `6ebe4e3217f5504757459545ce9eb34cbdce567213bf95cbb03b71dde5c1a1ea`; same_field `bb7e1b42ef796cc3eadd9a2f2750f39977a79c638ee9417e816cd9689b8acec4`; missing_journal `be9aec9b65ae8fe784a05f905d3b1022765932bc1c4c04078db6e47c50d06088`; sequence_gap `73b9403caa37e3bef9d22113ca59e5a469107d95b37e5c992a968363ad106887`; state_mismatch `b04151786cf30c40bdb247467946b1c9bea7b097403fc58009d4a0a1785fee4d`.

`FINAL_SHA256SUMS.txt` covers the freeze sources, result/qualification docs and all retained raw DBs, observations, outputs and process receipts/log bytes. Formal stages were not rerun to create this record.
