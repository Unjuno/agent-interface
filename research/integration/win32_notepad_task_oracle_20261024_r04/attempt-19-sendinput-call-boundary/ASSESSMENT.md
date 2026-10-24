# R19 assessment — simulated SendInput-entry stall

**Outcome: `PASS_SCOPED_BOUNDED_RECOVERY`; independent postflight: `PASS_POSTFLIGHT`.** The seam precheck confirmed the exact R17 generation and SHIFT-up, and verified that the producer-local `user32.SendInput` attribute could be substituted without invoking the native call. Runtime preflight then confirmed HWND 370739280 visible/enabled/foreground, blank, SHIFT-up, and generation `3e0505c367c9faf8aac8133e4620a9d1de06ce481d487eb7265906286406888f`.

The public supervised-Win32 program sent a real native SHIFT-down. The child producer reached the simulated `user32.SendInput` callable for SHIFT-up; that Python callable signaled entry and blocked before invoking the native function. Independent readback saw SHIFT-down. The cancellation request returned `pending`; later terminal action and retained cancellation both reached `recovered`, release was confirmed, replay denied, and the producer was retired. A same-generation readback saw SHIFT-up, with the document still empty and no emergency release.

The owner interval was 15.000 ms on the coarse monotonic clock and 16.976 ms at high resolution; margin to the 3 s cleanup deadline was 2.985 s. A separate process after MCP close confirmed the same generation, empty text and SHIFT-up. Task success remains null. The MCP close receipt's `release_confirmed=false` remains in raw and is not treated as evidence of key release.

## Scope limit

This is a deterministic Python substitution at the producer's `user32.SendInput` callable entry. It does **not** make the native Windows API or kernel hang. The recovery helper performs a real native release, but the producer-side fault is simulated. This narrows the boundary placement relative to R18; it does not prove a real in-API platform-I/O hang, arbitrary blocked-I/O guarantee, general reliability, process-restart transfer, task completion, stdio behavior, MAP01, efficiency or WSLc behavior.
