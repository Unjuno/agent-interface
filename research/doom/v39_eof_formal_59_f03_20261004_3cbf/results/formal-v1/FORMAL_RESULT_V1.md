# F03 pipe EOF/JSON formal result — v1

Disposition: **PASS — bounded four-cell gate**, with the independent saved-only result `VERIFIED_SAVED_PIPE_RECORD`. This is not a broad runtime, game, controller, safety, or production claim.

## H/T/D/C/U

- **H:** The F02 persistent typed reader preserves the ready/terminal FIFO and surfaces the expected repeated-wait failures for EOF/invalid JSON, compared with the exact E02 live-child EOF baseline.
- **T:** One fresh child in each fixed sequential cell: `baseline_eof`, `candidate_eof`, `candidate_events_eof`, `candidate_json`. No retries and no model calls.
- **D:** Raw per-cell rows, ordered source pins, unique child PIDs, two waits per cell with positive/ordered clocks, ready/terminal handshake, cleanup exit/liveness, native summary, external exit receipts, byte-identical native/export SHA manifests, and a separate read-only saved-data audit.
- **C:** One Linux/arm64 container on owned VM `research-6183-t0-20261003` (UUID `01M3ZD3J2GK283SQRFW9EW9DBZ`) using image `sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b`; `--network none`, one CPU, 1 GiB memory/swap, 128 PIDs, read-only root/source, UID/GID 501:501, dropped capabilities, `no-new-privileges`, private 256 MiB `/tmp`. The final entry receipt observed `cpu.max=100000 100000`, `memory.max=1073741824`, `memory.swap.max=0`, `pids.max=128`.
- **U:** Does not test a live GUI, model, DOOM/gameplay, controller integration, restart/concurrent-consumer behavior, normal-exit traces, causal latency, physical safety, host-wide contention/global resource bounds, or production adoption. The result only qualifies these four pipe-notification cells on this frozen Linux/arm64 setup.

## Observed cells

| Cell | Child PID | Two wait outcomes | Events | Cleanup |
|---|---:|---|---|---|
| `baseline_eof` | 44 | `TimeoutError`, `TimeoutError` | none | SIGTERM `-15`; child and reader not alive afterward; no cleanup faults |
| `candidate_eof` | 46 | `_SessionReaderFailure` / `EOFError` twice | none | SIGTERM `-15`; child and reader not alive afterward; no cleanup faults |
| `candidate_events_eof` | 48 | `_SessionReaderFailure` / `EOFError` twice | exact `ready`, then `terminal`; reader remained alive after `ready` | SIGTERM `-15`; child and reader not alive afterward; no cleanup faults |
| `candidate_json` | 50 | `_SessionReaderFailure` / `JSONDecodeError` twice | none | SIGTERM `-15`; child and reader not alive afterward; no cleanup faults |

All four producer row gates are `true`. Native summary lists the exact four-cell order, `retries=0`, `model_calls=0`, and `FOUR_CELL_GATES_TRUE_AWAITING_EXIT`. Native Docker state: exit 0, OOM false, started `2026-10-04T01:40:17.358437629Z`, finished `2026-10-04T01:40:18.409335984Z`. The observed row intervals are retained as monotonic-clock evidence; they are not presented as causal latency or performance measurements.

## Custody and audit

- Frozen source commit/tree: `0f8700502ef5778fb2b3f5a37123d5b983422c5a` / `eeba8542507ba9406a869f6ba93c532f4c6f86ae`.
- Exact eight-file input archive SHA-256: `8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5`; it is reproducible from the public frozen commit using the command in `PRELAUNCH_FREEZE.md`.
- Native container ID: `157779688bd0e6c4da743624e03023c43422d4fe1b83f86386d0357ea69b9d8f`; one start, exit 0, OOM false.
- Auditor container ID: `c1f3663f922c1c8a3ff8cb87716a3639bc9e52e3f2c6df6a35d67a24b4b2a681`; distinct saved-only invocation, exit 0, OOM false, started `2026-10-04T01:43:51.672634602Z`, finished `2026-10-04T01:43:51.796290252Z`.
- Native output and independent export each contain exactly five files (`SUMMARY.json` and four rows). Guest native/export SHA manifests match; recursive byte comparison passed. The host pull was independently re-hashed and compared with both guest manifests; host byte comparison and exact five-name inventory/summary gate passed.
- Saved-only auditor result: `VERIFIED_SAVED_PIPE_RECORD`, scope `saved-row-and-directory-semantics-only`; `AUDIT.json` SHA-256 `c7351e3c852d3e2f37e95576baee58013320fe4a7b72069651e1edd0febae5a7`.
- Full native rows, export rows, audit JSON, created/final Engine inspections, stdout, exit receipts, and SHA manifests are retained beside this report. Native/export row digests are in `receipts/native-data.SHA256` and `receipts/export-data.SHA256`.

This evidence supports the narrow distinction seen in the cells: the baseline's live-child EOF control timed out on both waits, while candidate EOF and invalid JSON surfaced typed failures on both waits; the event case retained ready→terminal FIFO before those same EOF failures. No causal attribution beyond this frozen synthetic comparison is made.
