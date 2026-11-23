# Win32 public runtime CLI Notepad task R03

Status: frozen before target launch or input

## Question

Does the repaired deterministic public runtime zipapp observe a fresh Notepad target, dispatch one token-and-save task, retain a verified terminal input release, and agree with an independent exact-file oracle?

## Frozen source and host

- Candidate source revision: `fc94a0b87175127100784c4843db7e428b86a3a9`; runtime payload change is limited to adding the already-promoted Win32 capture module to the distribution source list.
- Baseline main for packaged runtime payload comparison: `22aba58c276141401a7688be335be5191ec661b9`. Before target launch, verify every zipapp source file is byte-equal to its main blob.
- Runtime: deterministic public zipapp built and run with installed unpackaged CPython 3.12.12; standard-library-only Win32 path. No MCP/provider/model/network/dependency installation/Docker/WSLc.
- Target: fresh Notepad for exact empty path `target/task-r03-4DB219.txt`, bound to its observed HWND/PID/process path. No other window or document is in scope.

## Single attempt

Attempt ID `win32-notepad-public-cli-r03-20261124`; exact token `AI-WIN32-NOTEPAD-R03-4DB219`. Retain a read-only public CLI observation first. Only if fresh target generation and capture are returned, make one public CLI dispatch: focus selected HWND, type token once, Ctrl+S once, wait 250 ms, terminal `release_all`. Then take one read-only public observation and independently read saved file bytes. Exactly one dispatch is permitted. No retry or corrective input.

Any setup, target identity, observation, capture, validation, or foreground-admission failure stops without input. If dispatch/result or release is ambiguous, preserve target and evidence; do not replay, edit, or close it.

## Adjudication

Pass requires normal completed dispatch with positive input emission, verified terminal release and no unresolved cleanup, same pre/post HWND/PID/process identity, and exact UTF-8 token bytes with no extra file bytes. Retain all requests/results/images, task-file bytes, target identity, timestamps, process exits, and hashes. This one local attempt does not establish repeated reliability, expiry recovery, MCP/provider accounting, or comparative efficiency.

## Cleanup

Only after the result, independent score, and release are retained, close the exact experiment-owned window with normal WM_CLOSE. Preserve the target if effect/release is unknown.
