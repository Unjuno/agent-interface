# Win32 blocked-SendInput recovery probe — R01

Date: 2026-10-22. Current source: main `58a630ec07e7531906a0d72bc6ba9da3bc0b2f07`.

## Question and setup

Can the current `Win32RuntimeSession.recover_input()` neutralize an input when the native `SendInput` call has already accepted a key-down but has not returned to the backend?

`probe.py` runs the actual `Win32RuntimeSession.dispatch()`, `Win32Backend.execute()`, `key_state()`, and `release_all()` code with a fake `user32`. The fake records CTRL-down as accepted, sets its state down, and blocks before returning from `SendInput`. While blocked, a second thread calls the session's public recovery method. No Win32 DLL is loaded and no physical or desktop input occurs. This is an explicit scheduling fault model; it does not claim Windows itself blocks at this exact point.

## Results

Normal and optimized CPython 3.13.14 produced the same result:

- At the barrier, fake input state contained CTRL-down, while `backend.held_keys` was empty and `session.recovery_required` was false.
- Concurrent `recover_input()` returned `status=refused`, `error=INPUT_RECOVERY_NOT_REQUIRED`, `release_attempted=false`. It returned in 0.0012 ms but emitted no UP; CTRL remained down for the entire blocked interval.
- After the barrier resumed, the original dispatch continued, recorded the key obligation, and its ordinary terminal `release_all` sent UP. The final fake state was up and dispatch reported completed.

This does **not** prove bounded release under blocked platform I/O. It shows that a fast refusal can coexist with a held input, and that the current key ledger is updated only after the synchronous `_send_key()` call returns. `recovery_required` is also not set while the accepted send is still in progress.

## Decision and next discriminator

Keep the current result UNKNOWN whenever a native input call has not completed; the ordinary terminal release after barrier recovery does not certify the blocked interval. Any reviewed implementation design must cover two schedules separately: the native call accepts DOWN before blocking its return, and it blocks before acceptance so a concurrent UP might be ordered first and followed by a late DOWN. It must fence the original producer, bound the release path, independently read input state, and verify a separate fresh-target effect before claiming recovery. Prearming a ledger alone or sending a second UP alone does not close both schedules.

`raw/results.jsonl` contains both mode-specific trials and monotonic timestamps. `SHA256SUMS` covers the probe, this report, and the raw results. No WSLc/Docker allocation, real input, or application task effect was used.
