# Split-step release receipt correction 01

## H / T / D / C / U

- **H:** For one executor program, per-key explicit-up receipts remain buffered
  across successful steps until all backend-held keys are released. The backend
  then takes one owner-state sample and publishes the complete batch. Each row
  retains the step that issued its own key-up call.
- **T:** Against frozen PR #7355 head
  `3fdbeb0a9f6bbc158db879de71c890f28b719978`, begin with `held={a,space}` and
  release `a` and `space` in separate successful `Backend.execute` steps. Check
  whether both receipts are published after one empty-owner sample. Also check
  that an exception clears partial rows and that a new program ID does not
  inherit the previous program's buffered rows.
- **D — `PASS_CONSTRUCTION / HOLD_NATIVE_VALIDATION`:** At the frozen source,
  the new regression failed: the published release keys were `['space']`, with
  `a` missing. With the correction, 18 candidate backend tests, 11 retained
  adapter tests, and 8 retained owner-wrapper tests pass. Both per-key rows are
  published in release order after one sample; their step fields are `[0,1]`.
  A final `release_all` on the same worker also flushes previously buffered rows
  after one sample. An exception in a later step, while another key remains
  held, discards earlier partial rows and leaves no context. A completed batch
  stays published even if later code in that step fails, because its release
  and sample evidence is already complete. The separate program-ID test confirms
  old rows are not re-labeled into the new program.
- **C:** This is deterministic fake-owner construction evidence. It does not
  establish X11 delivery, physical key-up timing, application consumption,
  useful feedback, recovery, or task effect.
- **U:** No native GUI, X11, ViZDoom, model, container, or formal allocation ran.
  The release buffer can span ordinary program steps and the executor's
  `release_all` call on its worker thread. The isolated regression models that
  same-thread call order; it does not exercise a live X11 backend.

## Source and environment

The test-first failure used the unchanged backend from PR #7355 head above.
The corrected adapter stores incomplete receipts in its worker-thread-local
program context after successful steps, keeps each row's original step, and
clears the context on exception or after a verified batch flush. The original
`FREEZE.json` and `CONSTRUCTION.txt` remain unchanged and refer to the first
candidate. The correction's source hashes and local test outputs are recorded
in `SPLIT_STEP_FIX_01.json` and `SPLIT_STEP_FIX_01_CONSTRUCTION.txt`.

Environment: Windows host (`platform.platform()` reported
`Windows-10-10.0.26300-SP0`), Python 3.11.9. This method correction does not
authorize or claim the separately gated current-v39 X11 validation.
