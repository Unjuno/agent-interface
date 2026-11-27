# Win32 cancellation R32 — isolate the exact Q-up path

R31 captured four slow Unicode compensation key-ups before it reached the actual Q-up. R32 removes the text operation entirely while retaining one click, a save, and the intercepted Q-down. The fixture effect oracle requires `clicked=true`, `saved=true`, and an empty text field. The input-free preflight checks that the frozen operation list contains no text operation and matches that exact oracle, preventing the R31 sentinel mismatch.

Test-only wrappers time helper exchange, `_recover`, `release_all`, and `Win32Backend._send`, including the exact `VK_Q` key-up fields. One fixture, one dispatch, one cancel after hook entry, and one 1250 ms callback hold. No runtime source changes or input retries are permitted. Strict PASS still requires public release confirmation plus independent same-generation neutral readback before callback return.

A separate sibling packet records WSLc S01. That runtime smoke stopped before application execution because its pinned image was not cached; no WSLc operation is part of this native Win32 arm.