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