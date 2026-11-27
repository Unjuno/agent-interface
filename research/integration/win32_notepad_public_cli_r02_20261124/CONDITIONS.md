# Win32 public runtime CLI Notepad task R02

Status: conditions frozen before target launch or input

## Question

Does the repaired, deterministic public runtime zipapp observe a fresh Notepad target, dispatch one token-and-save task, retain a verified terminal input release, and agree with an independent exact-file oracle?

## Frozen source and host

- Candidate source revision: `3b24b97b3f` (full commit is recorded in the raw build manifest). It contains only the distribution source-list repair and import regression test on top of the frozen R01 evidence branch.
- Baseline main for packaged runtime payload comparison: `22aba58c276141401a7688be335be5191ec661b9`. Before target launch, verify every zipapp source file is byte-equal to this main blob. The only runtime packaging change is to include the already-promoted `runtime/backends/win32_v1/capture_artifacts.py`.
- Runtime: deterministic public zipapp, built and run with installed unpackaged CPython 3.12.12, standard library only. No MCP/provider/model/network/dependency installation/Docker/WSLc.
- Target: new empty file `target/task-r02-8A41D7.txt`; launch a fresh Notepad instance for this exact path and bind the run to its observed HWND/PID/path. No other window/document is eligible.

## Single attempt

Attempt ID `win32-notepad-public-cli-r02-20261124`; exact token `AI-WIN32-NOTEPAD-R02-8A41D7`. Retain a read-only public runtime CLI observation first. If and only if it returns a fresh matching target generation and capture, issue one public CLI dispatch: focus selected HWND, type token once, Ctrl+S once, wait 250 ms, terminal `release_all`. Then perform one separate read-only public CLI observation and independently read the exact saved file bytes. Exactly one dispatch is allowed. No retry or corrective input.

Any setup, observation, identity, capture, validation, or foreground admission failure stops before input and is recorded. Ambiguous dispatch/result means preserve target and evidence, with no replay or file edits.

## Adjudication

Pass requires normal completed public dispatch, positive input emission, verified terminal release with no unresolved cleanup, identical pre/post HWND/PID/process identity, and independent saved-file bytes exactly equal to the token (UTF-8) with no extra bytes. Save all requests/results/images, target identity, task-file bytes, timestamps, exit statuses, and hashes. This single local app run does not establish repeated reliability, expiry recovery, MCP/provider economics, or comparative efficiency.

## Cleanup

Close only the exact experiment-owned window by normal WM_CLOSE after all result and release evidence is retained. If dispatch or release is ambiguous, preserve it for diagnosis and do not close.
