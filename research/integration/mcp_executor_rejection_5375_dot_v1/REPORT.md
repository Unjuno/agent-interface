# First outcome: FAIL_PREWORKER_CAPACITY_RELEASE

## Finding

The unchanged public MCP server retained its single busy admission slot after a real executor rejected submission before the worker began. Restoring a healthy executor did not restore service for that server instance: a new harmless close request returned `busy`, with no invoke entry, no call-ledger entry and no operation artifact. An independent executor sentinel and a fresh server's close request succeeded on the restored worker.

This is an observed, deliberately injected executor-lifecycle failure in the current implementation. It does not estimate production occurrence, establish a general deadlock, or demonstrate an in-flight native-operation recovery failure. No backend/session was opened and no native input or external task effect occurred.

## Exact boundary and strongest baseline

Source main `1381412f270e94322e009a10e76e1aea7649cb7d`; unchanged source through pre-run main `fc1fb8a798bb8635c2dbd05d818b9fbfb85c8e9c`. Target `runtime/cli_v1/mcp_server.py` is Git blob `7227f105aa4481a6110cd384a038bc72aa0aabda`. The full actual module and dependencies were imported; no extracted miniature or weaker comparator was substituted.

`submit` acquires the real busy lock before `asyncio.to_thread`. A shutdown ThreadPoolExecutor rejects that scheduling request. The operation never reaches `invoke`, whose finally block is the only lock-release location. Removing the failed task from the worker set does not release admission. Transport cancellation shielding addresses a different boundary.

Existing tests cover overlapping admission, cancellation after work starts, backend failures and persistence failures. This allocation adds only the previously untested pre-worker scheduling rejection and capacity-restoration discriminator under Issue #5375's real-pool failure-containment question. #5410 is related resource-retention context; no new SCC/siphon policy is claimed.

## Fixed first invocation

Four `interface_close` calls and four observational `interface_results` list queries, with three fresh never-opened persistent owners and one pure executor-health sentinel:

| Case | Public result | invoke entries | Ledger calls | Retained files |
|---|---|---:|---:|---:|
| Untouched healthy owner | closed; isError=false | 1 | 1 | 3 |
| Actual shutdown-executor rejection | ToolError: cannot schedule new futures after shutdown | 0 | 0 | 0 |
| Same owner after healthy executor restoration | busy; operation_invoked=false | 0 | 0 | 0 |
| Fresh owner on restored executor | closed; isError=false | 1 | 1 | 3 |

The healthy sentinel completed between rejection and the recovery probe. Both successful closes retained `release_attempted=false`, `connection_close_attempted=false`, `authority_granted=false` and a closed owner state. Fail-stop native/backend tripwires were never called. Source-filtered thread profiling independently recorded exactly the two healthy invoke entries.

The separate raw-only auditor returned `errors=[]` and the failure disposition. Twelve data-only corruption controls were all effective and all rejected. Fabricated construction fixtures also exercised a coherent recovery result, so the auditor is not hardcoded to this observed failure. The scientific/runtime call sequence ran once; no retry, repair, source tuning or extra operation followed.

## Resources, provenance and warnings

CPython 3.12.14; installed MCP 1.29.0, pydantic 2.13.4, pydantic-core 2.46.4 and anyio 4.14.2. These versions differ from some repository CI environments and bound the integration observation. The source-level lock path is retained independently of that transfer limit.

Actual affinity `[0]`; RLIMIT_AS 268,435,456 bytes; RLIMIT_CPU 15 seconds; outer timeout 30 seconds; observed peak RSS 60,424 KiB. Outer exit is 1 because the original behavioral invariant failed. Stdout is empty. Stderr retains a Pydantic `IncompleteFieldDefinitionWarning` about the lifespan annotation; it is not suppressed or called clean stderr. No source/dependency change was made to resolve it.

The import-only preflight made no server or public call. It retained 560 loaded-file identities. The terminal inventory records 575 loaded files, including later stdlib/test-instrumentation/auditor imports. All frozen 49 files stayed exact before and after. Original source, construction failures, pre-run proposed freeze and process receipts remain immutable.

## Independent review

Separate pre-run review approved the full-module path, real rejected/healthy executors, profile observation, native guards, finite schedule, both-outcome oracle, controls and freeze. Separate first-outcome review used only read/parse/hash: all 49 frozen hashes, every receipt output, 575 terminal module hashes, exact public schedule, source-profile counts, empty rejected/recovery state and all 12 reconstructed mutation hashes reconciled. The reviewed disposition remains FAIL_PREWORKER_CAPACITY_RELEASE.

## Exact identities

- Freeze: `128e98156ab70ef8325d8861ede15ceae8dce9cbd3eb0b8956aa4f21f40cdb6f`
- Raw: `e1bb5e42de409f9701b3b5181e81ae85b2aaf1fe28857c4dfb1cd64183b4c5e2`
- Audit: `ff5b89d2028e60b027503aa12eddf7d58167ec4d173a4eab352d344f5a858ea6`
- Result: `e2a18ea01d2ccd1f5ee355bd34cbd128991915c5e9a40e6b8fd2df7b3bb0700f`
- Receipt: `c792ba0e745db733feeeb0338d1eb1c620662c8715bf743ce7aa637a8ce1329e`
- Terminal modules: `372703e46f9e0aa10fd223cdc92506cda153e660008b4e8b8336928a9172f39d`
- Controls: `47af3cec5983aeb4b9cd167ee17441902246c6f39d324487115a7083b3754a24`

## Integration decision

Preserve this original failure. A minimal repair must release admission on a proven failure before work begins while retaining exclusion for active workers and preserving transport-cancellation semantics. It requires separate source review and regression authorization; no production correction is included here. No GUI, model, performance, task-success, production-frequency or general-resilience claim follows from this finite injected boundary.
