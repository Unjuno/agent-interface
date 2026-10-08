# MCP invocation completion custody — ordinary integration repair

Existing #5539 comment5915748047 identified an unresolved composition after merged #5564: executor submission can raise after invocation starts, before its returned handle joins lifespan's shutdown set. The same source remains at base9c26e204c0475bee30919e3d0e6681f393078ef1, server blob05f952d26c90d66ccc2af3b24dd4704e0ffd596e. This repairs a concrete #57 correctness blocker; it adds no new computer-control mechanism.

## Decision and change

RETAIN this candidate for nonauthor review. Each acquired admission gets a loop-created completion future registered before executor submission. Pending revocation or invoke finalization acknowledges it once, after releasing the admission slot. Lifespan waits on these obligations, independently of a failed/missing scheduling handle. A shield protects the completion obligation if its teardown waiter is cancelled. A synchronous BaseException revokes only pending work and propagates cancellation/fatal exceptions unchanged; entered work still owns finalization. Public unknown-effect, no-replay, context propagation and exclusion behavior are retained.

The acknowledgment is at the end of invoke's resource-owning finally, after the call-ledger finished transition and slot release. It is not proof that the executor's OS thread exited or its lost scheduling Future completed. No hard bound is added to a worker blocked in native I/O. A directly cancelled lifespan still propagates cancellation and may require its caller to reconcile cleanup; the regression manually disposes only its inert owner after the worker finishes. This candidate protects invocation custody, not a new shutdown-recovery policy.

## H / T / D / C / U

H: an admitted invocation that entered must remain in shutdown custody through operation, report persistence and finalization even when scheduling raises or its returned handle fails/cancels. T: ordinary real public MCP/actual SDK, private real ThreadPoolExecutor threads, gated inert backend/session fixtures, seven added regressions and the complete affected four-module suite. D: shutdown cannot schedule owner close while the admitted invocation is gated; all106 methods pass, no discarded call or replay, existing pre-entry rejection/context/transport cancellation/overlap controls remain. C: faults are injected under the existing #5564 exception contract; normal healthy scheduling already supplies a usable handle. U: no natural OS failure incidence, actual native release/effect, GUI/model/token/latency, general runtime reliability or overall #57 completion inference.

## Retained actual results

| Ordinary stage | Runtime | Result |
| --- | --- | --- |
| First current-source four-case RED | native Windows / Python3.11.9 / MCP1.29.0 | 4 methods,4 failures, exit1 |
| First completion-custody repair | same initial environment | 4/4, exit0 |
| First affected-suite check | same; sparse distribution dependency absent | 103 methods,102 pass,1 setup error, exit1 |
| Unshielded completion counterexample | Windows / Python3.12.14 / MCP1.30.0 | 1 method,1 failure, captured InvalidStateError, exit1 |
| Original-source shutdown RED on supported runtime | same supported runtime | 4 methods,4 failures, exit1 |
| Shielded candidate | same supported runtime | 104/104, exit0 |
| Direct pre-entry cancellation RED | same supported runtime | 2 methods,1 failure/1 pass, exit1 |
| Final candidate | same supported runtime | **106/106, exit0** |

The first persistence-gate RED also records a secondary assertion during cleanup after its primary early-close assertion. It is retained rather than described as a clean single diagnostic. Pydantic's IncompleteFieldDefinitionWarning and Pillow deprecation diagnostics remain in successful stderr; successful exit is not warning-free execution. All stages are ordinary engineering regression/repair, with unique preserved outputs. No formal allocation or original research retry occurred. Separate3.12/MCP1.30 checks resolve a real support-contract mismatch, not a search for a favorable scientific sample.

The seven new methods cover synchronous raised error while reading, error during report persistence, failed and cancelled returned handles after entry, directly raised cancellation after entry, pre-entry cancellation/recovery through a new explicit close request, and cancellation of the shutdown waiter without corrupting completion notification. Existing99 methods include healthy completion, real shutdown-executor rejection, late revoked callable, propagated ContextVar, active exclusion, cancelled transport, guarded compiled ownership, public argument/clock boundaries and actual owned inert stdio/portable API paths. TEST_IDENTITIES.json retains the exact106 names. SDK fixture child exits are retained in full test logs; these are synthetic backend fixtures, not real desktop effects.

## Evidence and reuse

Every actual argv/start/end/exit/source hash and stdout/stderr is retained. source-* snapshots preserve exact executed server/session-test bytes; baseline/server and every intermediate candidate are separate. DEPENDENCIES.json records133 actual working source hashes and their Git blob IDs; only the server and session-test blobs change. SOURCE_NORMALIZATION.json explicitly checks normal Git CRLF-to-LF normalization and identical Python AST/locations; committed LF source is not called byte-identical to the preserved Windows execution files. environment312.json identifies actual Python3.12.14, SDK1.30.0, anyio4.14.2, pydantic2.13.4, relevant library source hashes and complete installed versions. This is an after-the-fact ordinary environment observation, not prospective formal preregistration.

Private originals remain in the author's owned output. PUBLICATION.json maps exact original/public hashes for path-only redaction; public receipts keep original stdout/stderr identity and are checked through that mapping. Hashes do not grant access to private originals or authenticate an arbitrary forged receipt. The data-only verifier checks publication/receipt/source/test identity closure; actual behavior rests on the retained executable regressions and independent review, not that verifier alone.

The archive has no test_* Python module, __init__ or producer. verify.py is an explicit stdlib data reader only. Runtime/workflow discovery is otherwise unchanged. A Draft PR and this local pass do not authorize main: prospectively fixed distinct nonauthors must give two explicit exact-head/digest content approvals, then review the actual-current combined tree and satisfy live GitHub/unique expected-old application conditions.

## Primary references and reproduction

[Existing finding](https://github.com/Unjuno/agent-interface/issues/5539#issuecomment-5915748047), [integration claim](https://github.com/Unjuno/agent-interface/issues/5539#issuecomment-5965852952), [#57 sequencing](https://github.com/Unjuno/agent-interface/issues/57).

The runtime uses [loop.create_future and thread-safe callback dispatch](https://docs.python.org/3.12/library/asyncio-eventloop.html), with [shielded waits](https://docs.python.org/3.12/library/asyncio-task.html#shielding-from-cancellation). Test faults deliberately construct concurrent Futures; no custom executor or automatic replacement policy is introduced into production.

In a supported Python>=3.12 environment with mcp==1.30.0, anyio==4.14.2, pydantic==2.13.4, Pillow==12.2.0 and python-xlib==0.33, run:

```sh
python -m unittest -v runtime.cli_v1.test_mcp_server runtime.cli_v1.test_mcp_session runtime.cli_v1.test_mcp_guarded runtime.cli_v1.test_mcp_clock
python -O runtime/results/mcp-worker-shutdown-01a0ff35-20261003/verify.py
```

No current/shared GUI/input/GPU/Engine/WSLc/model or main resource is held. Common fleet deadline is unknown and not reset. Broad computer-control integration/effect/efficiency goals remain open.


## Shared entry: retained FAIL, adoption HOLD

After the scoped106-method success, the exact existing local/CI entry `runtime/integration_checks/native.py` was actually run once on native Windows/Python3.12.14, with the CI-pinned MCP1.30.0/Pillow10.2.0/numpy1.26.4/python-xlib0.33. This later environment is separate in native-environment312.json; the earlier106-method/Pillow12.2.0 environment remains preserved. Native CI itself selects Ubuntu. Full commands,1728 source hashes, internal source-hashed result.json and full logs are retained. There was no timeout or retry of the shared entry.

**Shared result FAIL:** protocol419 methods,4 failures/30 error events/7 skips; harness205 methods,1 failure/39 error events. Error events can be subtests, so these are not converted into invented passing-method counts. Unchanged legacy native exchange/allocation/finish/cleanup require POSIX, os.O_DIRECTORY or /proc/self/ns/pid. Their Windows failures are not fixed by weakening their ownership contract.

A separately named three-method original-server diagnostic exited1: the no-inline-summary20ms lower-bound assertion failed at15ms and the Linux/X11 zip fixture's literal-slash assertion failed. The explicit-wait case passed that one original-source check, while both candidate time assertions remain retained failures; this does not estimate rates or prove causation for every failure. The archive module explicitly labels itself Linux/X11. Supported Python3.12.14 clock metadata reports monotonic=GetTickCount64/resolution0.015625s versus perf_counter=QueryPerformanceCounter/resolution1e-7s. This is consistent with coarse elapsed-time observation, not a measurement proving actual physical sleep duration. No repeated search for a passing timing sample occurred.

Disposition now has two separate levels: **RETAIN the scoped completion-custody repair for review; HOLD runtime adoption until appropriate compatible native verification and exact-current nonauthor review.** The broad shared suite and hosted/Linux CI are not called PASS. No new archive/test skip, unrelated POSIX/clock/zip repair or workflow change is bundled. The original server was restored only for the three-method diagnosis and the final candidate's exact working hash was restored and checked afterward.

Data-only -O verification of the initial70-file packet succeeded; its initial manifest is retained. Six separate semantic controls reject boolean exit alias, reversed UTC, missing method identity, wrong decisive SDK, wrong executed source and lowered reported denominator with outer byte checks intentionally lifted. These are consistency checks, not authenticated execution proofs. The final focused log records three owned inert SDK children exited0; later exact PID observation found none of those processes. Shared-entry first failures and every internal log remain public with qualified path-only redaction.
