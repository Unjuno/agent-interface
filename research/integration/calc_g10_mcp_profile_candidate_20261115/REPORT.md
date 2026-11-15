# G10 public MCP profile candidate — local evidence

## Result

The candidate wires the fixed `calc-g10-two-save-v1` profile through MCP preparation, owned compiled execution callbacks, parent-held per-action saved-byte snapshots, and post-close task verification. It preserves separate profile IDs and the existing `calc-ocr-save-v1` behavior.

Local validation on Windows, CPython 3.11.9, branch `codex/g10-public-profile-20261115`, base `b046c90d6ab80cedb47fcd1be85fac5111dfce0b`:

- G10 focused profile/artifact/composition/scorer: 25/25 normal and 25/25 under `-O`.
- Existing owned-process MCP suite: 74/74 normal and 74/74 under `-O`.
- Targeted MCP prepare and existing Calc owner integration: 2/2.
- `py_compile` and `git diff --check`: successful.

Raw command output is in `raw/`. The logs are stdout/stderr captures from local test invocations.

## Changes covered

- Public prepare selects a fixed G10 profile and rejects caller-supplied values/plans.
- G10 only accepts a parent-created two-save artifact and requires current reviewed aliases.
- Both action aliases resolve to the stable reviewed Calc menu keyboard anchor.
- A trusted pre-dispatch callback records the exact action ID, source evidence and generations before input; after verified input release, the matching callback snapshots the workbook bytes before another action can overwrite it.
- Parent call custody retains both save receipts; the verifier requires verified owner close, the exact target exit receipt, matching in-memory artifact descriptor, both receipts and the independently scored saved-byte snapshots.
- Expired reservations release both artifact-map references.

## Scope limits

These tests use Fake X and archived FODS fixtures. The composition fixture writes archived bytes from its test callback; it does not demonstrate that LibreOffice actually emitted the saves. No live Calc or MAP01 input was sent, no Docker/WSLc operation was performed, and no research allocation was consumed. The candidate does not establish live GUI correctness, provider token accounting, matched efficiency, or completion of issue #57.

The initial G10 profile OCR budget was set to one second. A local focused run exhausted that timing budget under the test host load; the bound was raised to three seconds and the tests then passed. The first attempt to collect focused test output passed all module names as one argument and returned nonzero; the command was rerun with a PowerShell argument array and succeeded. The corrected logs are retained; the unsuccessful collector output was overwritten and is documented here rather than represented as a product-test failure.

## Public Calc caller freshness follow-up (2026-11-15)

The existing owned-MCP Calc integration test intermittently failed during profile construction with `Calc entry must use the reviewed stable menu keyboard anchor`. A test-only point-resolution record showed the exact cause: the entry alias had the expected `[12, 8]` offset, but resolution returned `STALE` / `expired_or_nonfresh_observation` at source sequence 1 because the test relied on the 1.5 s default capture-freshness window across prepare, observe, mint, and compiled-call setup. The public code correctly refused stale evidence. The caller test now explicitly requests the supported 5 s freshness bound for both minted aliases. No runtime authority or freshness limit changed.

After the fixture change, the focused public Calc MCP call passed 1/1 in normal mode (9.213 s) and 1/1 under `-O` (10.141 s), Python 3.11.9. Raw output is in `raw/public-calc-mcp-normal-20261115.log` and `raw/public-calc-mcp-optimized-20261115.log`; the failing stale resolution is retained in `raw/calc-primary-public-mcp-failure-resolution.jsonl`. This confirms the existing `calc-ocr-save-v1` public caller fixture only. It is not an integrated G10 two-save run, live Calc evidence, or a MAP01/#57 result.

## Next evidence boundary

Before any live run, prospectively freeze a dedicated allocation/host record, source hashes, exact target generation, foreground/ownership conditions, stop path and artifact custody. Then validate the current G10 menu anchor, first and second distinct saves, post-release physical input state, exact target exit and parent-side scoring. Do not infer a matched efficiency result from this local candidate.

## Public G10 caller join probe and parent custody repair (2026-11-16)

A Fake X owned-MCP probe traverses launch, explicit window review/bind, the public G10 profile constructor, its real pre-dispatch/on-completion callbacks, two fixture-backed save receipts, owner close, exact target exit, and `interface_verify_task`. Its initial failure established two process-boundary gaps: the parent artifact was unbound while the child copy was bound, and the child-owned receipt records were absent from the parent object.

The parent now binds its artifact only from the owned Calc launch supervisor's reviewed binding and fresh metadata, with XID, PID, start ticks, process generation, window generation, focus and mapping checks. The child profile repeats its fresh identity query and rejects any difference from the parent binding. After execution, the parent adopts save receipts only when each ordered transition is release-confirmed and the request/receipt IDs match the parent descriptor; it re-reads each O_NOFOLLOW-protected snapshot and checks its digest, byte length and file identity before storing it in parent custody. Parent verification refuses if this adoption did not complete. A direct artifact test also mutates a receipt hash and confirms adoption rejects it.

Focused public G10 caller integration passed 1/1 in normal and optimized Python. Artifact parent-adoption suite passed 14/14 in both modes, including hash-tamper refusal. The existing public Calc caller passed 1/1 normal and optimized. Raw logs are `raw/public-g10-parent-custody-normal-20261116.log`, `raw/public-g10-parent-custody-optimized-20261116.log`, and `raw/g10-artifact-parent-adoption-{normal,optimized}-20261116.log`.

The full owned-process MCP suite ran 75 tests and ended with 5 failures and 4 errors on this host. Failures include source/mint freshness expiry, bounded method runtime exhaustion, and cancellation tests whose pending response raced asynchronous report cleanup (WinError 32). An affected window-metadata test was corrected to refresh only the synthetic source timestamp in its Fake owner, keeping the production 500 ms freshness policy intact; it then passed alone. An unrelated compiled-caller test still exceeded its fixture's 5 s method budget in an isolated rerun. The full-suite run is retained at `raw/owned-process-post-g10-normal-20261116.log`; it is explicitly not a pass.

Scope remains Fake X with a stub graph executor and archived FODS bytes. This establishes public-caller and parent-custody composition only; it does not establish live Calc save behavior, native input release, or GUI task effect.

A further negative public-caller case now covers parent-bind failure. The fake launch supervisor returns a reviewed binding with a mismatched PID; the public compiled call refuses with `CALC_LAUNCH_REVIEW_BIND_REQUIRED` before invoking the compiled operation or dispatching input, and creates no compiled artifact directory. The refusal test passes 1/1 normally and under `-O`; the positive public G10 caller still passes 1/1 in each mode after the new gate. Raw logs: `raw/g10-parent-bind-refusal-normal-20261116.log`, `raw/g10-parent-bind-refusal-optimized-20261116.log`, and the corresponding positive-caller custody logs. This is offline Fake X caller evidence only.

## Public G10 caller final targeted recheck (2026-11-16)

Re-ran the public G10 caller success path and the parent launch-review PID-mismatch refusal after the dispatch-gate change. Success path: 1/1 normal and 1/1 optimized. Refusal path: 1/1 normal and 1/1 optimized; operation and input dispatch remain false. Raw outputs are `raw/g10-public-positive-final-{normal,optimized}-20261116.log` and `raw/g10-parent-bind-refusal-final-{normal,optimized}-20261116.log`.

A fresh isolated run of `test_standard_compiled_profile_uses_generation_bound_owned_caller` still returns `SAFE_YIELD / execution_failed` with release verified, task success null, and replay denied. Its synthetic app pixel commit was written, but the expected compiled task result was not produced; the owner timing was 8.719 s on that diagnostic run and its journal was empty. A separate isolated Calc settle-caller run returned no `method_receipt` and `interface_close` verified connection close without an attempted release (`release_confirmed=null`). These failures are not converted to passes and were not fixed by raising the fixture budget. The attempted fixture-only budget adjustment was reverted. Existing full owned-process run remains 5 failures and 4 errors; suite is not green.

The standard-caller diagnostics are retained under `raw/diagnostic-standard-caller-20261116/`; preservation itself encountered a child-held journal file (`WinError 32`), so this diagnostic directory is incomplete and is not counted as a complete custody packet. No live GUI, Docker, WSLc or MAP01 input was performed.

The retained diagnostic raw was read back after the isolated failure. Initial/state synthetic BGRX frames are both 4,096 bytes and differ in exactly three channel bytes at pixel `(1,1)`; the fake application receipt records the synthetic commit 2.466 s after the graph action start and before the action terminal acceptance timestamp. The public method receipt still says `SAFE_YIELD / execution_failed`, `completed_transitions=0`, with verified release and no task success. The owner snapshot at that point reports the child alive and `review_required=true`; the journal is zero bytes while the owner holds it. The test teardown then remained blocked on that child until the diagnostic process was interrupted, so this does not establish a clean close or explain the backend's `execution_failed` source. The incomplete raw files now have their own `MANIFEST.json`; verify them as a diagnostic snapshot only, not a complete custody record.

## Compiled action failure layer check (2026-11-16)

Read-back of the diagnostic `.report.json.tmp` shows that the returned method receipt directly retained `action_terminal.status=execution_failed`; `runtime/core_v1/compiled_gui.py` maps any non-completed terminal status to `SAFE_YIELD / execution_failed` after checking release, and does not promote it. Thus the core classification is behaving as its tested contract requires. The source of the adapter/backend `execution_failed` remains unproven because the child journal and per-dispatch receipt were not successfully retained before that child stopped. Do not change the core outcome based on the synthetic pixel alone.

The `runtime.core_v1.test_compiled_gui` boundary suite passes 35/35 normally and 35/35 under `-O`; raw logs are `raw/compiled-core-contract-{normal,optimized}-20261116.log`. These tests validate status projection and deadline behavior, not the missing Fake X dispatch failure cause or owner close custody.

## Fake public-caller retention-mode contrast (2026-11-16)

Ran two counterbalanced pairs of the same one-action public compiled Fake X caller. The driver, graph (5 s deadline), action, point and result wait match after normalizing only the selected retention mode and output path. All four runs returned `TASK_SUCCEEDED`, one completed transition, release verified, effect succeeded, `task_success=null`, replay denied, and verified `interface_close` with confirmed release and owner exit code 0.

| Retention mode | Core elapsed median (n=2) | Owner elapsed median (n=2) |
|---|---:|---:|
| Files | 0.290 s | 0.437 s |
| Journal | 3.925 s | 4.602 s |

This is a local diagnostic contrast, not an efficiency comparison with matched durability: `runtime/guarded_x11_v1/COMPILED.md` explicitly says files retention is not fsync-backed crash durability, while `ReceiptJournal.append` flushes and fsyncs each record. The journal contains 38 records (46,796 bytes) for the recorded run. The result explains why durable custody may consume most of a 5 s graph budget on this Windows host and identifies a latency/durability tradeoff to investigate without weakening custody. The earlier journal-mode `execution_failed` remains unexplained; these two journal repeats succeeded, so do not claim journal mode alone caused that failure. Raw runs, scripts and paired condition/source hashes are in `raw/standard-caller-{files,journal}-mode[-r2]-20261116/` and `raw/standard-caller-retention-mode-paired-20261116.json`.

## Durable journal append cost probe (2026-11-16)

Re-appended the 38 payloads (46,796 source bytes) from a completed journal-mode caller run into a separate local journal, measuring each `ReceiptJournal.append`. The one-shot probe took 1.466 s total, median 37.2 ms, p95 59.2 ms, over the same 46,796-byte output. Each append performs canonical serialization/hash, write, flush and `os.fsync`; the probe does not isolate fsync from those other costs. This is about 37% of the paired caller's 3.960 s core median by rough cross-run comparison, so per-record append is material but does not explain the entire journal-mode delay. Do not remove or defer fsync based on this probe; that would change crash-custody guarantees. Raw replay journal, per-append timings, script and source hash are in `raw/journal-append-microbench-20261116/`.


## Current complete owned-process regression rerun (2026-11-16)

The complete `runtime.cli_v1.test_mcp_owned_process` module passed 76/76 normally (139.702 s) and 76/76 under `-O` (151.080 s) on CPython 3.11.9. The normal command output was observed directly in the local runner; the optimized stdout/stderr capture is `raw/owned-process-full-optimized-20261116.log`. The previously intermittent standard compiled caller also passed as an isolated test in both modes. This rerun does not erase the earlier retained 5-failure/4-error result; intermittent cleanup/focus behavior remains a historical diagnostic, not a currently reproduced failure. No live GUI, Docker, WSLc or MAP01 input was performed.


## G10 production CLI/stdio caller receipt join (2026-11-16)

Added `runtime.cli_v1.test_mcp_g10_production_stdio` and a test-only CLI entrypoint that runs the real `mcp_server.main()` under an MCP stdio client, backed by the existing Fake X owner and archived FODS fixtures. The client prepares the fixed G10 profile, launches/reviews the target, mints entry/save aliases, submits the public compiled call, and exact-call polls `interface_results` when launch first returns pending. It receives two release-verified save receipts, closes the session, then parent-side `interface_verify_task` returns verified/true from the two retained saved files. Local CPython 3.11.9 Windows reruns passed 1/1 normal (14.013 s) and 1/1 `-O` (14.377 s); the timing-annotated raw captures are `raw/g10-production-stdio-20261116/normal-timed-final.log` and `optimized-timed-final.log`.

**Startup limit boundary:** the first nested Windows stdio/owned-process run kept the production 5 s owner startup budget and returned `owned guarded process startup timed out` before target launch/input. To isolate the stdio receipt shape, the successful test-only server raises only its fixture startup wait to 20 s; it does not change production code. Measured `OwnedGuardedSessionOwner.get()` at 10.860 s normal and 11.031 s under `-O` (n=2; median 10.946 s), exceeding the production 5 s limit in this nested Windows spawn fixture. Thus the transport/custody join passes under the explicitly widened test-only wait, while the production 5 s nested-startup condition is a reproduced miss, not a pass. The initial timeout and intervening fixture corrections are itemized in `raw/g10-production-stdio-20261116/ATTEMPT_NOTES.txt`. This is Windows multiprocessing-spawn fixture behavior; it does not establish the Linux `fork` startup interval. Fake-only; no live Calc, MAP01, Docker, WSLc, or allocation use.

## Timing interpretation correction (2026-11-16)

The startup paragraph above compares the end-to-end `OwnedGuardedSessionOwner.get()` duration directly with `_STARTUP_TIMEOUT_S`; that comparison is not valid. Inspection of the current merged `runtime/cli_v1/owned_guarded_session.py` shows `process.start()` returns before the parent calls `rpc_parent.poll(_STARTUP_TIMEOUT_S)`. The 10.860/11.031 s `get()` measurements include process start plus readiness wait, while the 5 s constant bounds only the latter. The original default-budget run proves that no ready response arrived during that 5 s poll after `process.start()` returned; the captured timing does not isolate why. Keep the timeout result as a readiness miss, not as a measured total-startup limit violation. No Linux startup conclusion follows.

## Packet inventory audit (2026-11-16)

The root SHA-256 manifest lists 68 entries and verifies with zero mismatches. Six additional run-level `MANIFEST.json` files were checked: five declare complete custody, and `raw/diagnostic-standard-caller-20261116/MANIFEST.json` explicitly declares `incomplete-owner-journal-custody`. Every file listed in those six manifests matches its recorded size and SHA-256; the diagnostic is retained only with its explicit incompleteness and is not counted as a complete run packet.
