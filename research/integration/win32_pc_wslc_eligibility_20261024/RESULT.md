# Local PC eligibility and WSLc boundary (2026-10-24)

## Finding

This PC can run bounded native-Windows Win32 fixture tests. The R41 run used one owned fixture and one dispatch, and all launched processes exited. Its input-free preflight passed 11/11. The live caller then failed its first focus operation before emitting pointer or key input (`backend_emissions=0`, `input_dispatched=false`). The action remains UNKNOWN; no release or task-success sample was obtained.

The PC has WSL2 with an Ubuntu distribution and WSLg. The one-shot WSLc local probe R01 did not execute the pinned container task: the required image was not cached and the runner returned `WSLC_E_IMAGE_NOT_FOUND` with `--pull never`. No container task ran. This result establishes that the local WSLc image/runtime path was not ready for this probe; it does not establish whether a separately allocated WSLc host or a later image cache is available. R01 is consumed and was not retried.

## Evidence and limits

- R39: current-main runtime hash mismatch at input-free preflight (4/5 checks); no fixture, MCP caller, or native input.
- R40: referenced R36 predecessor evidence was absent from that clean checkout; no fixture, MCP caller, or native input.
- R41: preflight 11/11; release audit 2/10; combined audit 1/11; phase 2 not started. The single public dispatch failed foreground verification before any input emission. The retained action stayed UNKNOWN and close remained busy because the independent readback was non-neutral. Producer, sampler, fixture, and hook exited; foreground restoration passed.
- The new backend diagnostic was exercised by one native fixture regression run. It recorded `SetForegroundWindow=False`, a foreground handle different from the fixture target, and `backend_emissions=0`; the fixture task did not start. This confirms that the foreground request was rejected and the target was not foreground at the end of the bounded check. It does not identify the OS policy or process that caused the rejection. The regression remains FAIL for this run and was not retried.
- The focused diagnostic unit test passed; 35 related recovery, release, process-identity, and supervised-session tests passed. The native integration run remains failed at focus before input.
- WSLc local probe R01: pinned image missing; no container execution and no WSLc control evidence.

R39/R40/R41 raw packets and the R36 predecessor raw/audit are retained locally. The R39, R40, and R41 source packet files were compared against a separate local backup: 14/14, 14/14, and 37/37 files matched SHA-256. Public records intentionally omit host names and transient process, window, session, call, and operation identifiers. These summaries do not replace or modify the raw evidence.

## Next discriminating step

The backend now retains the `SetForegroundWindow` return value and observed foreground handle when its bounded focus check fails. A native attempt can proceed only under a fresh ID and frozen conditions; for this desktop, first arrange a user-authorized foreground path for the owned fixture, then verify focus without emitting input before any dispatch. Keep the no-retry rule. Use this PC for a WSLc experiment only after a separate fresh allocation or approved local image/runtime readiness is verified; do not pull/build the missing image as part of R01.

This record makes no claim about input release, task success, MAP01, WSLc GUI control, matched efficiency, broad reliability, or Windows foreground-lock causality.
