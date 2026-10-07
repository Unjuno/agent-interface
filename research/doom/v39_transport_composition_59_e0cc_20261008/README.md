# V39 fatal cover with planner write pressure

A fatal cover terminal must preserve the original error, prohibit later control admission, and retire a still-pending planner before the inner thread pool joins it. This current-main composition combines the narrow #8280 controller/adapter repair with #8320 bounded transport, retaining #8298 reply ownership and #8290 reaping/portability behavior.

The ordinary regression's baseline transport needed rescue after three seconds of demonstrated write pressure. The candidate raised partial-send uncertainty, refused the following interrupt send, aborted the pending transport, and reached the original cover error with every observed planner resource retired before fixture cleanup. This is a scoped integration result, not a live control or physical-release result.

## Exact source and scope

Base: `d4ac01bcb8bfc3a9eb13c8b00f43cb3ef02eccac`.

- Controller: only `require_cover_terminal`, the pending-cover validation/interrupt/abort block, and post-result terminal validation from #8280 head `e851a2e93c1b995fefa630c7e36a78680fc80e59`; 43 additive lines. No wholesale #8261-era controller overlay.
- Adapter: exact #8280 blob `e2566d063f9aeba77ea74a3996625fe80425d9f6`.
- Candidate transport: exact #8320 head `fd14d9ed655192b90c38c8509aa769f79f6fb745`, blob `515552361679a85ee3c75da0bc302aad2459b7aa`. Its reader is unchanged from current-main #8298 and reaping helper equals latest #8290.
- Process-tree tests preserve the four POSIX guards from #8290 head `9125b94f9de45db74503c7937e0fb9833a6cdf86`.
- Both arms otherwise load the same 19-module current-main research closure. Source snapshots and actual imported-module hashes are retained.

Earlier #8280 ACK/error/complete cells and #8320 client-only pressure cells did not cross this controller → adapter → actual Popen transport boundary. #7584/#7598/#7586 concern scorer/finish pipes. Finite targeted source/PR searches found no matching planner composition; this is not a proof of global absence.

## Retained final observations

CPython 3.12.14, macOS 27.0.1 arm64, host memory 64 GiB; `perf_counter_ns`, one observation per final cell, no statistical estimate. Load/free-space and exact commands are retained. One owned inert Python peer runs at a time. The peer stops reading after its turn/start reply; a 2 MiB synthetic concurrent request has an explicit 0.75 s timeout. The actual interrupt default remains 30 s and planner wait remains 90 s.

| Final cell | Outcome | Failed-cover to main exit |
|---|---|---:|
| Baseline pressure | FAILURE_RESCUED; baseline close also records PermissionError, leaving journal/stdout/stderr open until fixture cleanup | 3004.097 ms |
| Candidate pressure | SCOPED_PASS; 65,536/2,097,215 bytes uncertain, actual EAGAIN before cover error; no rescue | 734.566 ms |
| Baseline ACK + completion | SCOPED_PASS; cancelled answer not admitted; no rescue | 2.465 ms |
| Candidate ACK + completion | SCOPED_PASS; cancelled answer not admitted; no rescue | 2.456 ms |

Candidate pressure orders peer barrier → sender → actual partial write/EAGAIN → unavailable write lock/nonwritable fd → failed cover → send uncertainty → interrupt request_error → abort → future completion → actual outer cleanup. The original cover RuntimeError survives; exactly one synthetic submit and no final action occur. Before any fixture close, sender/reader/future are retired, child/group absent, three stream wrappers and journal closed, cached stdin fd cleared, writer lock available, and pending/reply maps empty. This does not prove global absence or reuse safety of every fd number.

120 focused tests passed across 20 controller/adapter/cleanup/transport suites. Five native-catalogue and 22 workspace-index tests passed; an initial index-module import failure due to missing `research` in PYTHONPATH is preserved, and only that failed module was rerun after correcting the invocation. Workspace inventory reports 160 indexed top-level directories. AST parsing and `git diff --check` passed for changed Python sources. No full remote CI or native Windows execution is claimed.

## First outcomes and independent audit

All three ordinary construction matrices are preserved separately. The first candidate-pressure cell failed before exposure because a readiness file was read before its JSON write completed. The peer barrier was repaired with an atomic rename. The second matrix observed the intended runtime behavior but some resource fields were sampled only after fixture close. Following independent review, the final matrix records those same fields before fixture close and binds all loaded research modules. Production sources, stimuli, deadlines and oracle stayed unchanged. These are ordinary harness repairs; no consumed formal allocation was replayed or historical failure replaced.

A separate nonauthor source/raw review is retained outside this source tree and will be referenced from the PR. The archive includes the original/updated protocols, harness versions, source snapshots, 12 cell traces and wire logs, execution receipts, focused tests, source staging failure, independent source-origin audit, retained-raw audit and mutation checks. `PUBLIC_REDACTION.json` records private-path-only redactions with original/exported byte hashes; private originals remain intact. Core source/harness and stdout/stderr receipt hashes remain exact. The independent auditor passed 470 named checks and rejected all 18 targeted in-memory mutations; root repeated that retained-only audit against the exported copy with the same result. The archive has 199 members and is 84,196 bytes.

Run `python -B research/doom/v39_transport_composition_59_e0cc_20261008/verify_evidence.py` to verify archived byte integrity without executing a peer. For semantic retained-raw verification, extract the archive into a fresh directory, then run `python -B independent-audit/audit.py --evidence-root .` using the auditor's documented CLI. The standalone `run_matrix.py` is an ordinary reproducible construction harness; it refuses to overwrite existing `runs-observed`. Reexecution is not required for retained audit.

## Limits

The real controller, adapter, transport, ThreadPoolExecutor and ControllerFailureCleanup execute. Scorer/input/observations are synthetic; the scorer handle reports exited, so outer cleanup exercises planner retirement without a real scorer. Actual receipts keep `cleanup_complete=false`, `scorer_terminal_observed=false`, and `input_release_verified=false`. Synthetic neutral terminals are not physical-release certificates.

The 0.75 s sender deadline is an injected contention condition, not a shortened production interrupt deadline or universal subsecond recovery guarantee. Serialization/journaling remain synchronous; close has multiple timeout phases. Close failure before waiter wakeup may still leave the pool waiting for the 90 s planner deadline. Live model, game, GUI, task effect, Windows pipe behavior, full resource containment and statistical latency remain unqualified.
