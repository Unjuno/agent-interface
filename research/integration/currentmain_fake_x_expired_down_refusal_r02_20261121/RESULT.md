# Current-main Win32 expiry-before-DOWN refusal regression — R02

## Scope and classification

This is a local rerun of one existing Win32-backend regression test in normal
and optimized Python. The backend is constructed without native Win32 bindings;
preflight and `release_all` are replaced with test doubles. This is synthetic
software-contract evidence, not a live Windows input test or formal allocation.

## Frozen source and conditions

- Current main at execution: `aecc24ccbe50735d2d27ede10a1f7b563ff4d2ae`
- Host shell: Windows PowerShell; Python `3.11.9`
- Test: `runtime.backends.win32_v1.test_integration.Win32SessionRecoveryTests.test_expired_operation_receipt_identifies_late_down_refusal`
- Test module Git blob: `6ea2e856d09b6409286840785e3199e1172d9071`
- Backend Git blob: `d362bc6c697786644ed1dd1f0dcb09a5d117f1a5`
- Frozen test condition: authority expires 20 ms after start; first operation
  waits 50 ms; second operation requests left-button DOWN.
- `release_all` is stubbed to return verified. No OS button/key event is sent.
- No Docker, WSLc, provider, application, or external resource was used.

The test expects `LEASE_EXPIRED_DURING_EXECUTION`, with operation receipts
`[5, 0, 0, 0]` for the wait and `[6, 0, 0, 0]` for the refused DOWN. This
distinguishes a post-expiry refusal from a sent input. It does not prove that
an already-held physical key was released.

## Results

| Mode | Result | unittest duration |
|---|---|---:|
| Normal | 1/1 PASS | 0.074 s |
| `python -O` | 1/1 PASS | 0.065 s |

Both command transcripts are preserved in `raw/`. The exact commands were:

```text
python -m unittest runtime.backends.win32_v1.test_integration.Win32SessionRecoveryTests.test_expired_operation_receipt_identifies_late_down_refusal
python -O -m unittest runtime.backends.win32_v1.test_integration.Win32SessionRecoveryTests.test_expired_operation_receipt_identifies_late_down_refusal
```

No independent auditor or mutation campaign was run. Assertions are those of
the existing test; no test or runtime code was changed.

## Limits

R02 complements [R01](../currentmain_fake_x_delayed_down_recovery_r01_20261121/RESULT.md): R02 checks refusal before dispatch after lease expiry; R01 checks conservative fencing after a delayed synthetic DOWN is observed. Neither verifies native physical release, live application effects, task success, efficiency, or reliability.
