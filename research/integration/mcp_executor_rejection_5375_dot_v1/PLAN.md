# Proposed full-runtime worker-submission rejection boundary

Status: proposal/construction only. Formal invocations: 0. No candidate repair exists.

## Scope and ownership

Origin: Issue #5375's unresolved real worker-pool fault-containment boundary. Issue #5410 is secondary resource-retention context; this is not another classical wait-cycle simulator. #5375's merged PR #5383 tested nine deterministic half-open/fallback transitions and explicitly excluded real concurrent workers. Existing recent #5375 toy results do not test the public MCP scheduler.

Source intake main `1381412f270e94322e009a10e76e1aea7649cb7d`; main, current goal and ownership are rechecked before freeze. Exact target module is `runtime/cli_v1/mcp_server.py`, Git blob `7227f105aa4481a6110cd384a038bc72aa0aabda`. The full `create_server`/`submit`/`invoke` implementation is used, not an extracted or rewritten miniature. `mcp_session.py` is blob `fcff15ed42a6c1eac26a2a0796f265ec4608a1e9`; current server/session test blobs are `2143c9995e7177ade0d8a20f6b348bf7468e75a1` and `3fff2126db9a89fd92467c4c2916555c016c6d2b`. SOURCE_READBACK.json pins all 22 retained module/test files by Git blob and SHA256.

Bounded issue/PR/branch searches for executor shutdown, thread-pool rejection, schedule-new-futures and MCP lock cleanup returned no identical active claim. Existing tests cover cancellation after a worker starts, overlap refusal and persistence/backend failures. None of those is executor rejection before invoke begins. Unpublished ownership remains unknown. Proposed local namespace is `mcp-preworker-5375-v1`; no new remote claim or source mutation yet.

## H / T / D / C / U

H: A rejected worker submission before the operation starts must not leave the public server's single admission slot permanently busy after worker capacity is restored. Source review predicts a gap: submit takes the lock, asyncio.to_thread may reject before invoke, and only invoke's finally releases the lock. This is a prediction, not an observed failure.

T: One bounded original-source diagnostic, using the real CPython ThreadPoolExecutor shutdown/rejection path and the full public MCP call path. Call only interface_close on a never-opened persistent owner. No native connection or external action can exist. Backend creation/selection/dispatch paths are fail-stop tripwires. All filesystem writes remain in a fresh study directory. Use a real healthy single-worker executor for controls and a real executor shut down before any work for rejection. No monkeypatched exception, artificial sleep or weak comparator.

Fixed sequence, with three fresh server identities/directories:

1. HEALTHY_CONTROL: one public interface_close call on an unopened server through the healthy executor must return closed, retain its ordinary receipts and execute invoke once.
2. REJECTION_BOUNDARY: install a separate executor that has already shut down. One public interface_close call must fail before invoke begins. Retain its exact response/exception, worker-entry trace, public results listing and on-disk inventory. Restore the still-healthy executor. A separate pure worker health sentinel must complete. Then issue one new harmless close request to the same unopened owner to test admission recovery. This is a controlled new request after proving no operation began, not automatic replay of an uncertain effect.
3. FRESH_SERVER_CONTROL: one close request on a fresh server using that same restored executor must succeed, proving the recovered executor and SDK can serve a new instance.

There are four public close calls total and one pure executor sentinel. Result-list queries are observational and counted separately. A source-filtered Python profile hook can record invoke-entry events without replacing invoke or submit; the exact observation mechanism must be reviewed before freeze. No source-level candidate repair is run. The independently implemented auditor reads only raw responses, inventories and entry records and imports no runtime code.

Concrete harness refinement before freeze: exactly four interface_results list queries follow the four closes, for eight public calls total. The list path has no worker or backend operation. threading.setprofile records only call events whose exact source filename and code name equal the unchanged nested invoke; it neither modifies nor replaces invoke/submit. Three empty server directories are created, with actual receipt bytes retained. A durable line journal records each request and response. Counts are derived from that journal and independently reconciled with raw rows; hashes/inventories are independently read from disk. Twelve effective data-only corruption controls run after an integrity-valid raw audit, including when the original behavior disposition is FAIL. They make no further public/runtime calls. Fabricated construction fixtures cover both a coherent original failure and hypothetical coherent recovery, preventing a hardcoded predicted outcome.

Import-only preflight completed once with exit 0, no stderr, source unchanged, observed peak RSS 57,408 KiB and no server or public calls. It records 560 loaded source/library files and their hashes. All loaded dependency bytes are checked before the formal import. Existing source and installed dependency bytes are never patched.

D: The required behavioral invariant is capacity conservation. FAIL_PREWORKER_CAPACITY_RELEASE is supported only if both healthy controls succeed, the first rejected call has zero invoke entries and no operation artifacts, the replacement executor sentinel succeeds, and the same original server still returns busy without invoking or producing a receipt. If admission recovers with an exact closed result, report PASS_PREWORKER_CAPACITY_RELEASE_SCOPED. Missing import/dependency/source/response/process evidence, inability to expose actual executor rejection, unexpected backend invocation, or timeout is STOP/HOLD. Do not infer success from internal lock state alone. Other behavioral outcomes are retained as explicit discrepancies rather than forced into the predicted result.

C: This injects an abnormal executor-lifecycle state; it does not estimate how often the deployed server reaches it. Normal server shutdown may prevent new calls via its shutting_down flag. Executor failure before a worker starts differs from cancellation after work has committed. A recovery executor replacement is a controlled discriminator, not a proposed production recovery policy. Existing global serialization remains the strongest actual baseline; no new circuit-breaker mechanism is assumed necessary.

U: No GUI, backend timing, device release, live task success, provider/model, security/exploit, throughput, human-tempo or general resilience claim. An unopened owner makes the close operation harmless; this boundary does not establish safe recovery from an in-flight consequential operation.

The raw field synthetic=false distinguishes an actually observed transcript from the explicitly fabricated oracle-construction ledgers. The executor-lifecycle fault itself is deliberately injected; this is not naturally occurring production evidence. The terminal LOADED_MODULES.json records actual module file identities/hashes after public invocation, including any lazy imports beyond the import-only preflight. No additional public operation is used for this inventory.

## Resource and integrity envelope

Existing own-cloud shell only; no Docker, package install, service credentials, network experiment or GitHub job. Installed dependency inventory currently reports mcp 1.29.0, pydantic 2.13.4 and anyio 4.14.2. Preflight is restricted to full-module imports and dependency/source identity, with no create_server, scheduler fault or public call. Record preflight separately and stop if imports fail rather than changing source silently.

Final invocation: one logical CPU; 256 MiB RLIMIT_AS; 15 CPU seconds; 30 wall seconds; one active worker at a time; no adaptive repetition. Freeze complete upstream/import graph, harness, auditor, synthetic-construction controls, exact request/schedule and dependency identity before the independent final review. Retain raw stdout/stderr, exclusive exit/command receipts, actual limits/affinity and source-before/after hashes on every terminal outcome. Preserve first FAIL/STOP without retry or tuning. A repair would require separate parent authorization after this original baseline is observed.
