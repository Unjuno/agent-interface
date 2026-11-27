# Win32 R13 setup readback — passed

**Disposition: `PASS_STATE_READBACK_SETUP`.** Frozen source: main `b529d1619fde73992d513e92601db980dcecc177`; one disposable Win32 fixture, Computer Use activation plus native foreground and SHIFT state readback only.

The fixture HWND was `12323886`. Computer Use returned a selected window with the same ID and successfully activated it while the probe was waiting. Native `GetForegroundWindow` then matched the fixture HWND. The witnessed SHIFT readback was boolean `false`; witness records identified the same HWND on the active `Default` input desktop. No key or task input was dispatched. The fixture recorded only `ready`, exited with code 0, and the pre-launch foreground value was restored.

The audit verifies frozen pretrial hashes, raw run hashes, activation/window join, native foreground, neutral SHIFT state with witness, no effect, and cleanup. This is only setup evidence. No post-expiry delayed action, input release, recovery, caller task success, or task effect was tested.