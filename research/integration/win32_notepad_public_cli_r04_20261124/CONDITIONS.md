# Win32 public runtime CLI Notepad task R04

Status: frozen before target launch or input

## Question

Does ordinary Computer Control activation of the exact experiment-owned Notepad window allow the repaired public runtime CLI to pass foreground admission, complete one text-and-save task, verify release, and agree with an independent file oracle?

## Frozen source and host

- Candidate packaging fix source: `fc1d28fef28e5411b0a5319094ae891ba417ff52`; the only runtime packaging behavior change is inclusion of the already-promoted Win32 capture module.
- Baseline main runtime payload: `22aba58c276141401a7688be335be5191ec661b9`; audit each artifact source blob before target launch.
- Runtime: deterministic public zipapp built and run with installed unpackaged CPython 3.12.12; standard-library Win32 path. No MCP/provider/model/network/dependency install/Docker/WSLc.
- Fresh target file: `target/task-r04-9C27E1.txt`; exact token `AI-WIN32-NOTEPAD-R04-9C27E1`; exact owned HWND/PID/process path must be recorded.
- After native target receipt, use Computer Control app/window enumeration to select exactly the one returned window whose title contains the exact unique filename, activate only that window, then read back its screenshot/focus state. Do not type through Computer Control. If enumeration is ambiguous or activation cannot be verified, stop before runtime dispatch.
- After activation, run a new read-only public runtime CLI observation and use its matching fresh generation as source for the one dispatch.

## Single attempt

One public CLI dispatch only: focus the selected target, type the token once, Ctrl+S once, wait 250 ms, then terminal `release_all`. Afterwards take one read-only public CLI observation and independently score exact saved file bytes. No retries or corrective task input. Any setup/admission failure before dispatch stops without input; ambiguous dispatch or release preserves the target.

## Adjudication

Pass requires normal completed CLI dispatch, positive input emission, verified terminal release with no unresolved cleanup, same HWND/PID/process identity, and exact UTF-8 task token bytes with no extras. Retain all raw observations, Computer Control activation/state receipt, dispatch request/result, images, target receipts, file bytes/hash, times, and exit statuses. This is a single local app case; it cannot establish reliability, expiry recovery, standard MCP/provider accounting, or comparative efficiency.

## Cleanup

Close only this exact experiment-owned Notepad window by normal WM_CLOSE after preserving task/release outcomes. Preserve the target if dispatch or release is ambiguous.
