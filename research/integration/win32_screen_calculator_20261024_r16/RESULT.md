# R16 result — physical-screen observation is usable for this target

## Disposition: READ_ONLY_CAPTURE_PASS

A single public `interface_observe` with `screen_physical_px`, over the same 320×533 client pixels as R15, returned a non-black image showing Calculator’s 1,043 display. Independent UIA preflight read the same value. The observation carried the same target generation as R15. The server remained supervised-win32, `call_count=0`, `input_dispatched=false`; `interface_close` completed with no unresolved calls.

This paired result isolates the capture problem: R15’s `window_client` capture was uniformly black despite correct client bounds and foreground focus, while the screen-physical route yielded usable pixels. R16 tests observation only; it proves no action, release, task oracle, recovery, efficiency or reliability outcome.

The raw wrapper, image, geometry, UIA read, close receipt and frozen hashes are retained in this packet. The observation image was visually checked and shows “1,043”.
