# R14 result — blocked-hook release boundary

**Outcome: FAIL_OR_UNKNOWN (19/20).** The one-shot public stdio-MCP attempt
completed the fixture task and its normal cleanup, but it did not establish
confirmed release while the native hook callback remained blocked.

The probe held one injected Q-down in the owned low-level hook callback for
700.934 ms after the public cancel response (650 ms requested). The cancel
returned `pending` in 1.431 ms. Eleven polls of the exact call ID all reported
action `running`, cancellation `pending`, and `release_confirmed=false`. At hold
end the hook callback had not returned. A separate process read same-generation
Q-up during the hold, but that Q-down was still blocked inside the hook and had
not reached the fixture; this is not evidence that a previously delivered key
was released. The single failing audit check therefore remains the intended
blocked-I/O release requirement.

After the probe released the callback, it returned 701.097 ms after the cancel
response. The exact producer exit was observed 701.311 ms after cancel; the
recovery Q-up hook event followed at 705.652 ms. The final same-generation
independent readback reported Q-up. The fixture independently saved the exact
R14 sentinel and journal prefix. Hook and fixture exited, the public session
closed, and the captured foreground window was restored. Public close itself
reported `release_confirmed=false`; runtime `task_success` remained null.

This run supports a narrow negative finding: this public caller did not confirm
release during a 650 ms retained callback. It does not prove that every Windows
input path behaves this way, that no later finite bound exists, or that an
independent hardware path cannot recover. The Q-up observation during the hold
is specifically non-discriminating because the injected down was still queued
behind the callback. Do not rerun R14 or rewrite its frozen audit/raw result.

Windows documentation explains why this boundary matters. [`SendInput`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
serializes injected events into the input stream. [`TerminateProcess`](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
starts termination asynchronously, and a process cannot exit until pending I/O
has completed or been canceled. [`LowLevelKeyboardProc`](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc)
runs on the hook-installing thread; Windows 10 1709 and later cap its configured
timeout at 1000 ms and can silently remove a timed-out hook. This is consistent
with R14's ordering, but the exact kernel scheduling cause is an inference. A
new R15 trial will keep the hook callback held beyond that documented maximum
and test whether the OS timeout permits exact producer retirement, supervised
recovery, and independent Q-up before the callback returns. It will be a new
attempt with a new sentinel and a frozen audit; R14 remains immutable.

Keep release `UNKNOWN` until an exact producer exit, same-generation release
receipt, and independent neutral-state readback are proved. R14 used this
user-authorized Windows PC and one owned fixture; no WSLc or Docker allocation
was used.

Evidence: `raw.json`, `audit.json`, `conditions.json`, `SHA256SUMS.freeze`, and
`SHA256SUMS.final`. The preflight passed with `native_input_sent=false`; the
formal probe ran once at source `5de12e91bdf8d0d589f429a4f0d3eb422ef2111a`.
