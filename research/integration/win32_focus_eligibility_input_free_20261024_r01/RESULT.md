# Win32 foreground eligibility, input-free R01 (2026-10-24)

## Result

**Focus subtest: PASS_SCOPED. Whole attempt: FAIL_OR_UNKNOWN.** The test froze against merged main `63238950bb95af29ab424e5b677773b4241e7ff5` and activated one exact, owned fixture through the authorized Computer Use window API. A separate process then called the Win32 backend `focus("fixture")`; the call returned, an independent foreground read matched the fixture HWND, and backend emissions remained zero. The backend closed successfully. The fixture recorded only its `ready` event; no click, key, release, or task effect occurred.

The owned HWND received one `WM_CLOSE` after its owner PID was checked. The fixture window and process were absent afterward, but the shell did not retain the process exit code. The frozen gate requires an observed zero exit code, so this attempt is **FAIL_OR_UNKNOWN** overall. Do not infer success from process disappearance. The attempt is consumed and was not retried.

## What this establishes

The same machine that rejected the R41 background focus request can pass the backend focus check after a user-authorized window activation. This isolates the earlier failure to foreground eligibility for that run; it does not prove the exact Windows policy or why the caller lacked foreground rights. Microsoft documents that `SetForegroundWindow` is restricted and can be denied while another window is active; `AllowSetForegroundWindow` itself requires the calling process to already have foreground permission ([SetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow), [AllowSetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-allowsetforegroundwindow)). No bypass, thread attachment, or system setting change was used.

The local WSLc probe remains separate: its pinned image was absent, so it ran no container task. This R01 used native Windows only and says nothing about WSLc eligibility.

## Evidence

The full local packet (conditions, runner, preflight, fixture events, focus result, UI readbacks, cleanup observations, independent audit, and SHA-256 manifest) is retained in the task's local `outputs` directory. Public reporting omits transient host/process/window/session identifiers. The independent audit reports `focus_subtest=PASS_SCOPED`, `overall=FAIL_OR_UNKNOWN`, `release_sample=false`, and `task_success_sample=false`.

## Next experiment

A new paired release-and-task attempt should use a fresh ID and current source, explicitly separate user-authorized foreground activation from program dispatch, and keep the controlling process handle alive through fixture close so it can record the exact exit code. Preserve the no-retry rule for this attempt. A foreground activation grants permission to focus; it does not establish release, recovery, or task success.
