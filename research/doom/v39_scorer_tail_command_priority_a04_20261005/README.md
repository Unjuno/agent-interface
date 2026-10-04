# V39 scorer-tail command priority A04

A04 extends the retained socket-readiness construction A03 with the uncovered
deadline-crossing callback boundary. A03 made the command readable during a
25 ms callback while the configured tail deadline remained open. A04 makes it
readable during a callback that finishes 25 ns beyond its deterministic 100 ns
tail deadline.

## H/T/D/C/U

- **H:** On the current PR #7692 head source, a command made readable during a
  callback that crosses the tail deadline will be reported as
  `CENSORED/command_ready`, retain `deadline_overrun=true`, remain unread inside
  the tail, and return through the normal iterator without another scorer
  callback.
- **T:** Run one deterministic sequence: verified release at 0 ns; a 100 ns
  tail; a callback from 0 ns to 125 ns that makes one newline-terminated
  command readable; then resume the same iterator once.
- **D:** PASS requires `command_ready`, `deadline_overrun=true`, one tail sample,
  zero reads during the tail, exact command delivery on resume, one total scorer
  callback, one iterator read, and one delivered command. Otherwise FAIL.
- **C:** Fake monotonic time and readiness are deterministic doubles. This does
  not model OS scheduling, buffer layers, or real callback cost.
- **U:** This validates only the frozen adapter boundary. It does not test real
  stdin, Doom, the full V18 session lifecycle, model behavior, game/task effect,
  recovery, survival, or MAP01 progress.

The test-first regression on the current PR head failed before the fix with the
expected `deadline_overrun` versus `command_ready` mismatch. The repaired source
then passed the targeted regression and the combined V1/V2 suites. The frozen
candidate and independent raw-only audit are retained under `results/a04/`.
This is construction evidence; no formal/live allocation was used.
