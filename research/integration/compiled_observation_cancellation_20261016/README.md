# Compiled semantic callback cancellation through the observation worker

2026-10-16 JST. Base main `b4f811ef5a4d1569d954137192a1f50cabe7809d`;
tested code `fe84e8739a7350bca719e231b41ce9dbccb2858d`.
Decision: **RETAIN_COMPILED_ISOLATED_CALLBACK_CANCELLATION**.
No runtime behavior or default option changes.

## Question and actual composition

The [native semantic repair](../compiled_native_dependency_repair_20261016/README.md)
adds read-only perception at native input checks. Does the existing explicit
observation-worker option still let this composed input owner clean up when
that semantic callback blocks while CTRL is held?

The probe traverses actual adaptive caller v3 → compiled helper v2 → form graph
→ guarded adapter → real alias store/NativeHandleBridge/backend/session. Both
routes select `process_identity=True, query_worker=True`; the isolated route also
selects `observation_worker=True`. Existing FakeX owner and separate read-client
fixtures replace platform construction, capture/XTest transport, keymap and
process evidence. Semantic value/effect recognition uses an explicit synthetic
phase pixel outside the target patches. No display/input, model/provider,
WSL/container or formal allocation was used.

After the first chord and its graph effect complete, the second chord presses
CTRL. The semantic callback then waits on a probe-owned Event before `a` can be
pressed. Cancellation uses the actual bridge token; expiry crosses the original
native lease by adding an offset to an otherwise advancing host monotonic clock.
Core/caller clocks continue normally. Event records separately retain real host
monotonic timestamps; injected expiry is not elapsed physical time.

## Six conditions per normal / actual optimized mode

| Route | Condition | Before callback resume | Final evidence |
|---|---|---|---|
| Isolated | Cancel | Owner returned; fake keys up; reader still live, pending and retired | Prefix1, EXECUTION_INCOMPLETE, verified fake cleanup |
| Isolated | Original expiry | Same | Same |
| Synchronous | Cancel | Owner still live; CTRL held; no result | After explicit resume: prefix1 and verified fake cleanup |
| Synchronous | Original expiry | Same | Same |
| Isolated | Stable | No blocked callback | Two chords/prefix2, TASK_NOT_VERIFIED |
| Synchronous | Stable | No blocked callback | Same |

Each stopped row emits the first complete chord, second CTRL press and CTRL
release: no second `a` press or replay. The outer verifier is skipped on partial
execution. Stable cases retain unavailable outer effect, never task success.
The synchronous control's observed live thread and held-key bitmap are part of
the result; a cancelled flag alone cannot unblock its synchronous callback.

On the isolated route, fake release and caller return occur before callback
resume is requested. The reader's delayed completion cannot change the returned
caller/core receipt, advance the published sequence, emit a suffix or restore
old admission: a subsequent admission is association_changed with no authority.
Late diagnostic files may still be written; the artifact directory is not
claimed immutable at caller return. Capturing final raw waits for those owned
reader threads to exit. All owned query/observation threads are closed and joined.

## Verification and retained material

Six new methods are registered once in the harness. The affected selection
passes **56 modules / 391 unique methods**, zero failures/errors/skips in normal
and optimized Python. It includes the prior semantic repair selection; this is
not all native/platform suites. 93 selected Git/worktree source/data joins,
complete streams, process IDs, optimization flags, conditions and two full raw
record archives are retained. Source selection is not an import closure.
CONDITIONS' base denotes the tested code; inherited old_prs is historical only.

Raw rows include before-resume results, actual Python thread liveness, fake
bitmap/emissions, worker retirement/pending snapshots, host event order, final
caller/core receipts and exact bridge files as hex. The saved-only reader checks
caller/core/native-terminal/release joins, the two routes' opposing event order,
late authority refusal and six copied contradictions in each reader mode. It
imports no candidate and performs no real application scoring. The `.py.txt`
runner/reader files are inert references with their original local bindings.

During local construction an initially fixed fake clock made all six methods
fail: the core correctly rejected post-action captures older than its real
effect timestamp, so the intended callback boundary was not reached. The fixture
was corrected to an advancing clock plus expiry offset before the source-pinned
run. That initial console output was not retained as a separate full raw packet;
it is not evidence of a runtime regression or a formal allocation result.

## Remaining limits and next boundary

This qualifies selected Fake X callback isolation through the compiled caller,
not universal finite release. Test Events and join watchdogs are not native time
bounds. Input transport, cleanup sync/readback, a stalled X server, process death
or synchronous user code outside this selected guard can still block. Default
synchronous behavior remains explicit in the negative control. Trusted callback
accuracy, independent app effects, finite semantic recovery and matched/domain
economics remain unqualified. Keep #17/#59/#57 open. Next distinguish a blocked
read-only dependency from blocked input/release transport in the supported
caller without introducing another input writer or false verified readback.
