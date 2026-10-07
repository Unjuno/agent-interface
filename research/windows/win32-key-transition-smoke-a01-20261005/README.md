# Win32 key transition host smoke A01

The one-shot probe passed on the active Windows host with a process-owned foreground `STATIC` HWND and one synthetic Shift DOWN/UP pair. `SendInput` returned success for both edges; the backend's `GetAsyncKeyState` samples changed false→true→false, with the same hold and backend IDs. Terminal `release_all()` also reported no keys or buttons down.

The retained trace has a third `cleanup=true` UP attempt: the backend re-sends UP during terminal release because the explicit UP remains an outstanding obligation until neutral-state verification. Its post-sample was up (`OS_KEY_STATE_ALREADY_UP`), and terminal release verified neutral. The independent result audit passes.

The observed nanosecond fields fell in identical host clock ticks for both transitions; they establish event order in this synchronous trace but do not support a latency estimate. The probe did not call core admission or `Win32RuntimeSession.dispatch()`. It establishes only this host's Win32 API behavior in this controlled sample: no physical keyboard hardware state, application delivery, third-party target behavior, task effect, UI compatibility envelope, or general reliability claim is made.

The initial runner import-path stop is retained in `STOP_FIRST_LAUNCH.md`; no candidate input was sent before that repair. The formal candidate ran once. Full inputs and classifications are in `result.json`; H/T/D/C/U is in `PLAN.md`.
