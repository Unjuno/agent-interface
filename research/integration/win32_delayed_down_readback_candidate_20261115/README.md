# Delayed DOWN readback regression — candidate evidence

Date: 2026-11-15 (Asia/Tokyo)
Branch: candidate/pr10303-current-main-reconcile-20261115
Base commit: b197edbe7666b7521261a98ef858ce5d4b05a4a3
Python: Python 3.11.9

## Change

The existing multiprocessing Fake-helper scenario now explicitly requires the observer's post-injection readback to report the obligated key as pressed. Event order is recorded as recovery completion, initial neutral readback, delayed old DOWN injection, then observed non-neutral readback. The owner must remain UNKNOWN, release-unconfirmed, task outcome unknown, replay denied, and refuse a new operation.

## Results

- Focused normal: 1/1 passed. Command: python -m unittest runtime.guarded_win32_v1.test_process_cancellation.ProcessCancellationTests.test_delayed_down_during_recovery_horizon_keeps_owner_fenced
- Focused optimized: 1/1 passed. Command: python -O -m unittest runtime.guarded_win32_v1.test_process_cancellation.ProcessCancellationTests.test_delayed_down_during_recovery_horizon_keeps_owner_fenced
- Full module normal: 31/31 passed (14.593 s). Command: python -m unittest runtime.guarded_win32_v1.test_process_cancellation
- Full module optimized: 31/31 passed (14.644 s). Command: python -O -m unittest runtime.guarded_win32_v1.test_process_cancellation

## Scope

This verifies a synthetic multiprocessing helper contract. It does not demonstrate native Win32 late OS input, physical key release, live GUI/MAP01 effect, efficiency, or reliability. No Docker/WSLc/native GUI operation was performed.

## SHA-256

- runtime/guarded_win32_v1/test_process_cancellation.py: 6460c50d5caa8e04e04b9cde5a94b2948d923f2f9b18de64068c9a74e23626f4
- normal.log: e607aed11c6996dc180fb8cf10842e0ebf1f4c8718f09b9f46a4a506203b5096
- optimized.log: 3c4af960149bc935f54949b04f8fcb6ea82bfb216099fe372b4af8d79282ac83
- module-normal.log: 21ce1a0506b5dd23619eb451accdca7918bda1c3a9ada3332e3fb6e8c1767d5f
- module-optimized.log: 3bfb45218d22053699180f4b2710027563af7bbb6f5032c8dc85e741e9ce1300

## Exception UNKNOWN → pending recovery → exact-call receipt → fresh caller

Test: runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_stdio_exception_unknown_then_fresh_generation_recovery

The production stdio test first reads the producer-exception action as UNKNOWN with release unconfirmed, then carries that action's operation ID, generation, obligations and conservative custody into a separate recovery server. The recovery test adapter completes its 2 s horizon, then delays its terminal receipt for 8 s. The public recovery call therefore returns pending after its bounded wait; the test confirms its call ID, operation and nested source custody, polls only that exact call ID, and confirms the terminal recovery receipt preserves source UNKNOWN, release/horizon evidence, null task success and replay denial before invoking the compiled caller against the fresh generation. The fresh task receipt remains bound to the fresh caller's own dispatch call ID.

Results: 1/1 passed normally (13.983 s) and 1/1 under -O (14.099 s), Python 3.11.9. A first invocation used an incorrect unittest class name and failed before test collection; retained separately as setup-error-wrong-test-class.log. Corrected invocations passed.

Scope: production CLI/stdio and public caller composition using Fake process/supervisor/readback/oracle fixtures only. No native Win32 input, MAP01, physical release, efficiency or reliability claim.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py fdc0586200a8a9e7a00047b2693afe0cd457aa3d682ee9bc0b1113d136f8cef1; exception-recovery-exact-query-normal.log 53c7acb107a0d7866287484a542d193d0ae0e32a25ab8b4c1241f6c30b7b8942; exception-recovery-exact-query-optimized.log 9750acbf799352b7738922c1f5760ecec2f7e425ecf85b59f33b6db207e2b60c; setup-error-wrong-test-class.log 4b204c64baf3125112ebee90a45b8d7042da0310ec84d45b8acae71bf381d1ac.

## Full public Win32 MCP regression module

After composing the exception-UNKNOWN → pending exact-call recovery → fresh caller path, the complete runtime.cli_v1.test_mcp_supervised_win32 module passed 49/49 normally (107.097 s) and 49/49 under -O (93.874 s) on Python 3.11.9. Both raw module logs are retained. One test invocation before this run used a wrong unittest class name and failed before test collection; see setup-error-wrong-test-class.log. It is not counted as a test failure.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py fdc0586200a8a9e7a00047b2693afe0cd457aa3d682ee9bc0b1113d136f8cef1; mcp-supervised-win32-normal.log 0290dac9356f30fdcc1ac1323f44898460deec0dbf3f0f44e5409d2f89a81560; mcp-supervised-win32-optimized.log 64dc3352d7896b49302460b6bbf754f3e072cc51de8d1ab09404d9a134906b7a.

## Read-only native target gate (observed 2026-11-15 12:01:42 UTC)

A read-only host check observed the existing R269 GZDoom process still responding. The recorded custody fence remains unresolved at revision 888 for the original UNKNOWN source operation. No dispatch, recovery, focus change, or process close was performed. The R269 packet's gate says not to continue or replay the source action until a genuinely fresh target generation and separately admitted recovery are available. This leaves native MAP01 work on STOP; it does not release the live target or resolve custody.

## Invalid recovery receipt fails closed through exact public lookup

Added test-only `--recovery-invalid-horizon` fault injection. The fixture returns an inner supervisor receipt claiming `recovered`, release confirmed, and a verified two-second horizon, but records only one observation. The production owned-session receipt validator refuses to promote that malformed shape. Through the production CLI/stdio, the outer recovery call stays pending until the bounded wait ends; exact-call `interface_results(call_id)` then returns outer `unknown`, source action still `unknown`, release false, task success null, and replay denied. No fresh caller is started on this failed recovery path.

Focused case: 1/1 passed normally and 1/1 under `-O` (10.775 s / 10.850 s). Full `runtime.cli_v1.test_mcp_supervised_win32`: 50/50 passed normally (101.020 s) and 50/50 under `-O` (101.578 s), Python 3.11.9.

Scope: test-only Fake supervisor/readback through the production CLI/stdio result path. This confirms conservative receipt validation and retrieval shape only; it is not native input/recovery proof.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py e86237f851622efcc38d69a9d18da2c385fcd826debb8f02a9e76fbfd44f58a5; runtime/cli_v1/mcp_supervised_stdio_test_server.py 537b09ce5ca20ca373db255a306c900d9791ae613709c507df97dc4edc70d798; invalid-horizon-exact-query-normal.log b22f951ae773ac331f06adb893694faa45a67e159b209628faea94da3a8bce71; invalid-horizon-exact-query-optimized.log f5aee400f27945e1de245a6d09eab0e3b0f5ed9cb69b895198d7334e3b9138fb; mcp-supervised-win32-invalid-horizon-normal.log 19b03993e2fca487e339bb9fe5a872f4e357fcc1cf43487721666ec52e003e7d; mcp-supervised-win32-invalid-horizon-optimized.log 49efc2952578d1a66b026c220fbbec24b06ae7a32c95cf595a3c62a8eba456dd.

## Failed recovery blocks the next same-generation public dispatch

Extended the invalid-horizon production-stdio case: after exact-call retrieval remains UNKNOWN, the test invokes the public standard dispatcher with the recovery generation. It is refused with ORPHAN_RECOVERY_UNRESOLVED, operation_invoked=false, input_dispatched=false, task_success=null, and replay_allowed=false. This directly checks the live owner admission fence after a failed bounded recovery; no producer/input operation is admitted.

Focused test: 1/1 normal (10.939 s), 1/1 optimized (10.497 s). Full runtime.cli_v1.test_mcp_supervised_win32: 50/50 normal (102.091 s), 50/50 optimized (102.877 s), Python 3.11.9.

Scope remains Fake-backed production stdio and owner gate only; no native Win32 or MAP01 proof.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py CD4B078E98E36ECBF24BFFDB8AD223AC931EEAA88579F8F1DDEE9FC879ADDC75; invalid-horizon-gate-normal.log 7EC14A6D33236FB58FD2C155C0CC631F450CC9EB1CF1DDD6938111D188E0C451; invalid-horizon-gate-optimized.log 337415DC19B1E6C3F70A30998A95CC99A26DCC38DC2B197E219D4C4F700A6002; mcp-supervised-win32-recovery-gate-normal.log 9035A8E1E9AA6174CC96B1698D8874C32DC1C8CA96D4AAAD85EDCD3BC99F9B24; mcp-supervised-win32-recovery-gate-optimized.log 4F6FC1FD66A38C2CC359E448424016F851A54F0D0F3E4F196095FF65BF60D298.

## Exact recovery lookup keeps the control receipt under compact presentation flags

Extended the delayed-success production-stdio exact-call recovery test to repeat the terminal lookup with `compact=true`, `report_refs=true`, and `detail=brief`. The lookup retains `recovered`, `release_confirmed`, the verified 2 s horizon, source UNKNOWN, null task success, replay denial, and `operation_invoked=false`; it does not acquire generic image-review fields. This confirms unsupported presentation modes preserve the full control receipt as documented for failures/unsupported reports.

Focused test: 1/1 passed normally (9.621 s) and 1/1 under `-O` (8.999 s), Python 3.11.9. The complete `runtime.cli_v1.test_mcp_supervised_win32` module passed 50/50 normally (102.253 s) and 50/50 under `-O` (115.469 s). Raw focused logs: `exact-recovery-presentation-normal.log` and `exact-recovery-presentation-optimized.log`; full module logs: `mcp-supervised-win32-exact-presentation-normal.log` and `mcp-supervised-win32-exact-presentation-optimized.log`.

Scope: Fake-backed production CLI/stdio presentation contract only; no native recovery, MAP01 effect or efficiency result.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py F46EFAF1DAF62FA2C3F729991AD2AC94A0BD85F33915F85D013678FDD72D2BD4; exact-recovery-presentation-normal.log B2E690A835FA50223DE4680FB74D8462BB9EF6A9A830123E7E66A9BC990C0625; exact-recovery-presentation-optimized.log EE80FBBD2612900A0F12A6DD118348CEECDB84164AE71FD1D8117B3B5E5D657A; mcp-supervised-win32-exact-presentation-normal.log 9D97A21028A066CE883546BA488AE9B8C509E80D9B2509D6DA19AD310ED57F54; mcp-supervised-win32-exact-presentation-optimized.log 50E09F4B3D7D9BE8C4EC48B4CB48AB3886D490B8D050CB627D9EF4D232D45DB8.

## Compact exact recovery query composed with the public fresh caller

Strengthened `test_stdio_exception_unknown_then_fresh_generation_recovery`: the producer-exception source remains UNKNOWN, separate recovery remains pending until exact-call lookup, and the terminal lookup now requests `compact=true`, `report_refs=true`, `detail=brief`. The same path checks retained source custody, verified 2 s release horizon, `task_success=null`, replay denial, and fresh-generation requirement before `run_public_compiled` dispatches a separate attempt. Its task oracle remains bound to that fresh dispatch call ID and expected generation.

Focused composition test: 1/1 passed normally (13.394 s) and 1/1 under `-O` (13.306 s), Python 3.11.9. Raw logs: `exception-recovery-compact-caller-normal.log` and `exception-recovery-compact-caller-optimized.log`.

Scope: production CLI/stdio and public compiled caller composition with Fake target, supervisor, observations and task oracle. This closes a presentation-to-caller integration assertion only; no live Win32, MAP01 task effect or #57 efficiency claim.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py F98D9DEAC2F41B794DFF10B9B68E513E9A79E8C9442B0B56A36A6F9886A9AF79; exception-recovery-compact-caller-normal.log 4C01929BA96C13551F35CB11F615A3CF3EBA05B53E848E7E1333DC9801035C83; exception-recovery-compact-caller-optimized.log B6B2B6FDC3B8B4EEC4F232CACC751DE0F37C778B7E469388DF427C335DCE1705.

## Recovery query to compiled caller requirement crosswalk

| Requirement | Enforcement / evidence | Verification | Scope limit |
| --- | --- | --- | --- |
| A delayed recovery remains pending under its own call ID; unrelated IDs cannot receive its receipt. | `interface_results(call_id=...)` exact-call lookup. | `test_production_stdio_orphan_recovery_pending_exact_query`; includes unrelated-ID query and terminal compact/brief lookup. | Fake supervisor/readback via production CLI/stdio. |
| Impossible or incomplete horizon evidence must stay UNKNOWN and block same-generation public input. | Owned-session recovery receipt validation and owner admission gate. | `test_production_stdio_invalid_recovery_horizon_exact_query_stays_unknown`; verifies exact receipt remains UNKNOWN and dispatcher refuses before input. | Fake failure injection; not an OS race proof. |
| Exception UNKNOWN custody must be carried into separate recovery; only verified release/horizon permits a later fresh-generation attempt, whose task oracle binds to its own call ID. | Public recovery receipt fields plus `run_public_compiled` dispatch/task-oracle join. | `test_stdio_exception_unknown_then_fresh_generation_recovery`; now retrieves recovery using compact/brief flags before the fresh attempt. | Composed Fake target/provider/oracle; not live MAP01 effect. |
| A retained pending dispatch is classified as delivery-uncertain only when exact call, generation, operation, release custody, neutral readback and recovery evidence match. | `supervised_win32_compiled._terminal` / `_verified_recovery_custody`; public caller exact-result join. | `test_public_compiled_caller_joins_exact_result_query_and_task_oracle`. | Contract regression; does not independently establish physical input state. |

Compiled caller source SHA-256: `runtime/cli_v1/supervised_win32_compiled.py` FD1478A424585956ECA2CA62F54D485E778D5688C2D3E2504181151B2231ED98. These checks make the selected handoff path reviewable; they do not satisfy #57's all-attempt lifecycle/economics report or replace R175's narrower native HUD result.

## Actual compiled caller exact-result query in compact presentation modes

Extended `test_public_compiled_caller_joins_exact_result_query_and_task_oracle` so the caller's own `resolve_pending` callback retrieves both the normal completed dispatch and the later producer-exception UNKNOWN dispatch using `compact=true`, `report_refs=true`, `detail=brief`. The successful attempt still joins exact call/generation and reaches its one positive task oracle. The exception attempt still classifies as uncertain with release unverified and does not call effect or task verification. This exercises `_terminal` over actual retained public dispatch result shapes through the server, rather than only testing recovery-tool result presentation.

Focused caller integration: 1/1 passed normally (1.427 s) and 1/1 under `-O` (0.840 s), Python 3.11.9. Raw logs: `compiled-caller-compact-result-normal.log` and `compiled-caller-compact-result-optimized.log`.

Scope: Fake process/input/effect and task oracle through the public caller/server path. It verifies result classification and oracle suppression; no native input, MAP01 HUD outcome, or efficiency claim.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py 3B4FD2FB0F108E8ED7B690F0A011E36CBCE6A4DA59DE841C7E19139270CD9094; compiled-caller-compact-result-normal.log 484377055B71513BECE8383E4888945CA0DC53B36FB6180098DE5BB700807652; compiled-caller-compact-result-optimized.log 2F85F36C54811C7BFB212E2B61F02DE35B74752FC773C3482448AC67A2A579D0.

## Compiled caller retains UNKNOWN when exact result includes recovery release

Strengthened `test_stdio_public_compiled_caller_preserves_unknown_exception` so its public `resolve_pending` callback reads the exact result with `compact=true`, `report_refs=true`, `detail=brief`. The retained exception action stays UNKNOWN even though its cancellation record reports recovered/release-confirmed. The compiled caller classifies delivery as uncertain with release unverified and does not call its effect verifier or task oracle.

Focused production-stdio caller regression: 1/1 passed normally (1.481 s) and 1/1 under `-O` (1.192 s), Python 3.11.9. Raw logs: `compiled-caller-unknown-recovery-compact-normal.log` and `compiled-caller-unknown-recovery-compact-optimized.log`.

Scope: Fake-backed public caller/server classification. Release recovery alone does not establish task effect; no native MAP01 or #57 efficiency claim.

SHA-256: runtime/cli_v1/test_mcp_supervised_win32.py 57EC76D4017C1AB3081C084A8ADE7916E0F3C79E70E069409D225B08E4E6A06A; compiled-caller-unknown-recovery-compact-normal.log CCF012FEAAECC1716B977AFCA94DAF593ACD807EB7833BE641DB9E3142D5FA00; compiled-caller-unknown-recovery-compact-optimized.log 3E727791EBC16B32EC6B8A64DABBDE7B619AA93F6CE91F6220847EBE1702B8BC.

## Read-only native custody gate (2026-11-15)

GZDoom PID 41580 remained responsive with title `Hydroelectric Plant - Freedoom: Phase 2`. The authoritative custody fence remained `unresolved`, revision 888, with pending `button:map01:left` and `key:map01:SHIFT:virtual_key`, operation `bb1c1f207e34407db20c28703713ae6a`, source generation `3b8649...f393c6f`, and no `last_resolved` entry. No focus, input, recovery, or process-close operation was performed. Native MAP01 remains gated.
