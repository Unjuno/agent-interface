# Win32 public runtime CLI Notepad task R01

Status: frozen before target launch or input

## Question

Can the current-main public runtime CLI use the promoted Win32 backend to
enter one unique token in a fresh Windows Notepad document, save it, and retain
a normal-completion release receipt that agrees with an independent file
oracle?

## Frozen source and host

- Source baseline: current main `22aba58c276141401a7688be335be5191ec661b9`.
- Runtime package: deterministic `runtime.distribution_v2` zipapp built from
  frozen experiment commit `85d001cfdfde48d96c525c4d1057f2772a46b46a` with
  unpackaged CPython 3.12.12. This commit adds only this experiment's frozen
  condition file; a pre-build `git diff 22aba58..85d001 -- runtime` must be
  empty, and the artifact manifest's runtime-file hashes will be compared to
  the exact main tree before use.
- Runtime invocation: `python agent-interface-runtime.pyz dispatch` under
  unpackaged CPython 3.12.12. The runtime build and CLI use only the Python
  standard library for this Win32 path. The host's CPython 3.13.14 WindowsApps
  environment has MCP 1.26.0 rather than the documented 1.30.0; therefore this
  attempt deliberately does not use or qualify the MCP transport.
- Target: one explicitly selected HWND belonging to the new
  `C:\Windows\System32\notepad.exe` document created for this attempt. No
  existing user document or browser window is in scope.
- No network, model/provider, Docker, WSLc allocation, dependency installation,
  or external service is used.

## Single attempt

- Attempt ID: `win32-notepad-public-cli-r01-20261124`.
- New target file: `target/task-r01.txt`, initially zero bytes.
- Exact task token: `AI-WIN32-NOTEPAD-R01-6C2D9E`.
- Read-only observation precedes dispatch and supplies the exact target
  generation. One public runtime CLI dispatch contains: focus the selected
  Notepad target; enter the token once; send Ctrl+S once; wait 250 ms; perform
  the required terminal `release_all`.
- A separate read-only public runtime CLI observation after dispatch captures
  the target once; it cannot issue input or replay the action.
- Authority lease: 30 seconds from immediately before the single dispatch.
- The result packet retains the exact observation and dispatch JSON requests,
  complete JSON results, capture images, the task file bytes, target HWND/PID
  identity, process exit, timestamps, and SHA-256 manifest.
- Exactly one dispatch call is permitted. No retries or second task action.
- If setup, observation, target identity, foreground admission, capture, or
  pre-dispatch validation fails, stop without input and preserve the stop.
- If dispatch or result retrieval is ambiguous, do not replay, close the target,
  or alter the task file. Preserve the target and raw custody for diagnosis.

## Frozen adjudication

Full pass requires all of the following:

1. Public runtime CLI dispatch returns normal completed status and records positive
   input emission.
2. The retained runtime receipt reports verified terminal release and no
   unresolved cleanup.
3. The independent oracle reads exactly the frozen token from the fresh file,
   with no extra bytes or additional write; the file hash and byte length are
   retained.
4. The pre- and post-dispatch target identity is the same selected HWND and
   process identity; the exact CLI request/result, images, output bytes, clocks,
   and hashes are retained.

Any failed or unknown condition is a failed/partial attempt, never a retry.
This one attempt can support only a scoped basic task-effect/normal-release
observation on Notepad through the public runtime CLI. It does not test the MCP
caller, expiry, delayed operations, recovery, reliability, same-window
recovery, provider accounting, model calls, or efficiency against a comparator.

## Cleanup

After the result, independent file score, and release receipt are preserved,
close only the Notepad instance/window created for this attempt. Keep all
conditions, raw reports, images, the saved task artifact, and hashes in this
packet. Do not close a window if the dispatch/release outcome is unknown.
