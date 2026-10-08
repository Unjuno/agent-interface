# Issue #4698 construction and preflight history

Allocation `needle-resident-checkpoint-6842711-6842713-6842717-v1`. These are construction-only events; none consumes or substitutes the formal allocation. The chronology is append-only, and failed records are retained.

## Container availability

- Cached image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64; Docker client and server both reported 29.8.0. No pull/install was attempted.
- First smoke command supplied nonexistent `docker run --timeout`; Docker returned usage/error 125. No container started.
- Second command redundantly passed `python` to the image's Python ENTRYPOINT; image attempted `/work/python` and exited 2.
- `--workdir /` plus the same redundant argument attempted `//python` and exited 2.
- Correct invocation pins `--entrypoint /usr/local/bin/python`; minimal read-only, no-network, 1-CPU container printed `container-ok` and exited 0 in about one second. Docker did not freeze.
- First bind mount embedded literal PowerShell quote characters and was rejected by Docker's mount parser. Passing the resolved host path as one PowerShell argument fixed the mount.

## Construction test and source defects

- Initial test run caught a Python syntax error before any optimizer step. Corrected before proceeding; formal count remained zero.
- A later 5-test construction run caught a missing base-training `BATCH` constant after the one-arrival treatment was narrowed. Corrected; no formal data were touched.
- `construction-final2.log`: 5/5 construction unit tests pass. A later final-source run also passed 5/5 and AST parsing (`AST_OK`).
- A first online smoke exposed a mismatch between one-arrival mode and the resident request loop; retained as `smoke-trainer.log` (exit 1, `resident_shutdown`). The mode was corrected.
- Next smoke exposed a `flush` argument passed to `json.dumps` (`smoke-trainer3.log`, exit 1); corrected before successful smoke.
- First successful single-arrival trainer smoke (`smoke-trainer4.log`): respawn 1,916.159 ms, resident 35.585 ms; not an efficacy or formal measurement. Its first auditor launch wrote into read-only raw input and exited 1; added a separate audit output mount.
- Re-audit caught auditor reference-list shadowing, then a smoke-vs-full schedule count mismatch. The auditor was corrected; old results were kept separate rather than overwritten.
- `construction-smoke-v5`: one-arrival trainer completed (respawn 1,935.832 ms; resident 79.133 ms). Auditor checked 2/2 snapshots, rejected 5/5 corruptions, found zero integrity errors; disposition `HOLD_LATENCY_BUDGET` is smoke-only and has no formal standing.

## Full-path preflight (not formal)

- Exact bounded Docker settings: `--network none --pull=never --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges`, source read-only, raw results separately read-only to auditor, audit output separately writable.
- `construction-smoke-v6`: all 3 seeds × 12 feedback arrivals completed. Independent auditor: 72/72 snapshots, request bindings and prediction states matched; base/input and durable-byte hashes verified; worker input omitted support pool/schedule/labels; 5/5 corruption controls rejected; zero errors. Disposition forced to `CONSTRUCTION_ONLY_AUDIT_PASS`, never formal PASS.
- Preflight resident p95: seed 6842711 = 200.497 ms; 6842713 = 109.711 ms; 6842717 = 111.038 ms. Respawn p95 respectively 2,150.798 / 2,012.082 / 1,990.989 ms. Resident was faster than respawn but exceeded the 60 ms absolute gate for every seed; the formal hypothesis is therefore already unlikely to pass.
- `construction-fullpath.log` and `construction-full-audit.log` retain the raw compact outcomes; raw JSON and independent `AUDIT.json` are retained in the corresponding construction directory.
- One earlier full-path audit invocation exited 2 because the then-current audit incorrectly expected 16 feedback results instead of 12 while also conflating the 16-row support pool. This was an auditor defect, not a scientific FAIL. Corrected auditor subsequently passed all 72 construction snapshots; old STOP/error output was not overwritten.

No formal source freeze, formal trainer orchestration, or formal optimizer update has occurred as of this record. Any later formal run must use the exact source/image/command hashes in `FREEZE.json`, execute once, and keep its raw outcome even on STOP/FAIL/HOLD.
