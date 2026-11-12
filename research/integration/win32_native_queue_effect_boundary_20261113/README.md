# Native Win32 input release does not imply application quiescence

R149 produced one task effect **691.4841 ms after the verified two-second
input-state horizon ended**, after the exact public action had reported
`recovered`. An accepted A key record remained in the native Windows message
queue during the deliberately filtered application schedule. Resuming ordinary
dequeue and WndProc dispatch incremented the fixture's task counter once.
No reconstructed keyboard message was used. Input release and task effect were
observed separately; the public result correctly kept `task_success=null` and
`replay_allowed=false` before and after the effect.

This is a positive, scoped counterexample to interpreting neutral recovery as
"no later application effect." It is **not** a failure of the existing scoped
input-state receipt, which did not claim task completion. It is one controlled
native-Windows fixture, not spontaneous late OS delivery or MAP01 completion.

## All attempts and the method repair

| Attempt | First outcome | Consequence |
| --- | --- | --- |
| R147 | Method failure; source action UNKNOWN and release unconfirmed | First `PM_NOREMOVE` preview raised `AttributeError`: the ctypes field is `hWnd`, not `hwnd`. Its unresolved durable obligation and all original raw are retained. |
| R148 | PASS, bounded orphan recovery only | One public UP-only request used a separately observed new fixture generation. The exact source producer was absent; 78 observations covered 2.0007131 s, with a 31.0749 ms maximum gap. Both generations were fenced, durable custody cleared, and the source action stayed UNKNOWN. No ordinary dispatch or task effect. |
| R149 | PASS, scoped queued task effect | A fresh target and corrected method retained the same timing and outcome criteria. One dispatch, automatic expiry, verified release/horizon, then one delayed native task effect. No fallback cancel or replay. |

The R147 error was reproduced without input using real `ctypes.wintypes.MSG`
storage and a fake transport: the dispatch regression failed before correction.
Assigning a lowercase Python attribute does not write the native `hWnd` field.
The corrected fixture passed two ABI tests normally and with `-O`. R149 also
passed its four protocol tests in both modes. R147's frozen files were not
edited, and its failed attempt is not removed from the record.

## Frozen conditions and observations

Runtime source: `0284b68b1c69612736c0ecf7a1d1fb84871e30a9`;
runtime tree: `24c84540abb65d56ed0646ea9a0889b51c4a7e67`.
The user-authorized local Windows PC used CPython 3.14.2 and
`QueryPerformanceCounter()` (reported resolution 100 ns), through the existing
public MCP `supervised-win32` route and the known Codex-origin custody view.
No model calls, Docker, WSL, runtime installation or global input-setting change
was involved. This does not qualify launcher-independent custody continuity.

The program focused one fresh owned fixture, sent A-down, waited 50 ms, sent
A-up, and entered a 15 s wait. Authority expired at the public execution-clock
sample plus 4 s. The fixture serviced non-keyboard messages, previewed keyboard
records with `PM_NOREMOVE`, and kept them in the OS queue until the recovery
terminal plus 650 ms. It then used normal `PM_REMOVE` and immediately dispatched
the OS-returned structure. The maximum hold was 20 s and lifetime 180 s.

| R149 observation | Value |
| --- | ---: |
| Authority expiry, monotonic ns | 262847357442000 |
| Recovery release receipt, monotonic ns | 262847380075400 |
| Two-second horizon end, monotonic ns | 262849380883600 |
| Exact terminal observed, monotonic ns | 262849399688300 |
| Task counter increment, monotonic ns | 262850072367700 |
| Effect after authority expiry | 2714.9257 ms |
| Effect after horizon end | 691.4841 ms |
| Horizon observations / maximum gap | 78 / 35.2109 ms |
| Independent asynchronous A samples | 623; 3 down before expiry |
| Independent samples after terminal | 92; all neutral |

These are timestamps and intervals of one controlled schedule, not benchmark
speedups. Sampling does not establish continuous neutrality. The recovery UP
attempt appears at several nested receipt paths; there is one distinct
retained recovery UP attempt, not three independent attempts. The native queue
also retained the program's earlier UP. An API insertion return, neutral
readback, and WndProc consumption are different observations.

The preregistered auditor passed all 23 checks. A separate implementation by
the same worker passed 16 raw-path/source checks and rejected six in-memory
alterations: missing post-horizon preview, wrong dequeue window, early effect,
missing down sample, task-success upgrade, and duplicate effect. This is not an
independent-person review claim. Both successful fixtures exited normally;
post-run exact-process queries found the fixtures exited and producers absent.
The final custody journal was clear at revision 375 and A was sampled neutral.

## Historical r09/r10 interpretation

The retained [r09](../win32_live_delayed_input_recovery_20261110/r09/fixture_app.py)
and [r10](../win32_live_delayed_input_recovery_20261110/r10/fixture_app.py) sources
assign `replay_message.hwnd = hwnd` when constructing a new ctypes `MSG`.
The native field remains null in the verified ABI test. Their "dispatched"
events record reaching the API call, not proof that the intended WndProc ran.
This is a concrete method defect compatible with their missing task effect;
no historical live rerun or exclusive-cause claim is made. Original files and
first results remain unchanged. R149 instead leaves messages in the OS queue.

## Integration decision and remaining work

Retain the existing separation: `recovered` attests the scoped release/readback
protocol; task success and replay authority remain separate. A finite neutral
sampling horizon must not authorize a generic "all old effects drained" claim.
Before overlapping a new logical task with an old target, use a target-specific
effect/postcondition check or an independently justified target transition.
A fresh observed generation alone is not evidence that an old application
queue was drained.

Next useful work is to compose this distinction with the existing independent
task-effect verifier and MAP01 caller, then run the same-model, all-attempt
comparison tracked by [#57](https://github.com/Unjuno/agent-interface/issues/57).
Do not infer arbitrary delivery bounds, a general 20 ms guarantee, MAP01
completion, reliability, or model/provider efficiency from these three runs.
No runtime behavior or merge protection was changed by this evidence package.

## Evidence and preservation

[EVIDENCE.json](EVIDENCE.json) is an explicitly selected public derivative with
the full A-state sample array, all non-ready fixture events, matching action
and recovery records, timing, audits, source pins and manifest identities.
Host paths, full session envelopes, executable locators and images are omitted
from that selection. Exact original sources are copied as non-executable
`.py.txt` evidence; they are not imported or discovered as tests. Preregistrations
are retained separately. Raw packets remain in task-local private storage:

| Packet | Files read back and hash-verified | Manifest SHA-256 |
| --- | ---: | --- |
| win32_queue_residency_20261113_r147 | 66 | `3984eb52391c20a527ab1308baaf7a5833fffa8834c9fab3d547108cc4bc19a7` |
| win32_orphan_recovery_20261113_r148 | 50 | `3cbe956b81016fa9745a9e7cb002f15f4fe7ff7c10583766ceea4bce8f9b1f97` |
| win32_queue_residency_20261113_r149 | 165 | `c1a161054fd24e45c85c1ae57f19c927387bd5f9c6202d609688fcd3a90b3017` |

The [public integrity inventories](raw-manifests/) retain an ordered size/hash
entry for every retained file but omit private path locators, including session
filenames. Complete original manifests stay with the private packets. They
exclude only regenerable Python bytecode and each manifest itself. All 281
files matched on readback. Hashes do not replace the original raw, which was
not deleted or rewritten; complete packets are not publicly published here.

API semantics were checked against the primary
[PeekMessageW documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-peekmessagew)
and [DispatchMessageW documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-dispatchmessagew).
The concrete ctypes field behavior was measured on the pinned local interpreter.
