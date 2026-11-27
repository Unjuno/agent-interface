# Win32 zero-state query witness

`GetAsyncKeyState` returns zero both for a currently-up key and when its query cannot access the active desktop/foreground thread. A zero sample therefore cannot retire input custody by itself. The production backend only treats a zero sample as UP after bracketing it with matching availability witnesses that establish all of the following:

- the configured target is still the foreground HWND;
- `OpenInputDesktop` succeeds with read-object and hook-control access and `UOI_IO` says that desktop receives input;
- the caller thread, foreground target thread and input desktop have the same desktop name;
- the caller token integrity RID is at least the target process integrity RID.

If any fact is missing or changes across the sample, the backend retains UNKNOWN custody. The target associations for key and button downs must be preserved to scope this evidence. The read-only R02 diagnostic confirms those facts and raw zero values for one owned fixture on this host; it does not prove release of a prior injected event. Only a separate public live effect trial can qualify the path.

The witness uses synchronous Win32 calls and makes no hard timing guarantee. It does not prove bounded release while a platform call blocks, generalize across desktop/session/privilege configurations, or establish independent application effect. Those remain separate gates.
