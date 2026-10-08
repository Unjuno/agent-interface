# V39 per-key measured-release scorer-tail A01

This construction experiment tests whether the frozen V39 per-key event schema
can define a bounded scorer-only tail without converting
`input_release_measurement` into the legacy `input_release_transition` schema.

## H/T/D/C/U

- **H:** Given the frozen A03 fake-display admission/up pair, the strict adapter
  can join exact program/step/key/owner/token/actuation identity, require
  confirmed physical edges and an empty backend-held set, and set the tail
  boundary to the upper endpoint of the physical-up measurement interval. A
  ready command remains unread by the tail and is delivered exactly once by the
  ordinary scorer iterator.
- **T:** Run the adapter, V18 compatibility, V19 composition, and socket
  readiness unit tests against the frozen trace. Linux WSL runs the core tests;
  Windows runs the full focused suite including controller flag selection.
- **D:** PASS only if the validator yields boundary `87811364949416` for the
  unchanged raw pair, rejects relabel/identity/confirmation/held-state
  mutations, the socket case returns `command_ready` with zero tail samples,
  and the next iterator read returns `finish` once. Both required test runs must
  pass, except for the pre-existing Windows anonymous-pipe skip.
- **C:** A release transition may be faster to integrate, but it does not carry
  the distinct V39 physical-up interval. This test may still pass because the
  supplied pair is a single fake-display key cycle and the backend state is
  supplied by a fake composition.
- **U:** No X11 server, ViZDoom game, OS input, planner, live allocation,
  application consumption, threat exposure, useful feedback, recovery, or task
  effect was measured. WSL used the installed Ubuntu distribution, not WSLc;
  WSLc was unavailable. WSL lacked Pillow, so controller-import/flag tests ran
  only in the Windows focused suite.

## Reproduction

Run the commands in `COMMANDS.txt` from the repository root. `FREEZE.json`
records source and input hashes. `RESULT.json` records both environment-specific
test runs. `audit.py` independently rechecks hashes, the raw admission/up
identity and interval, the decision gates, and test dispositions; its output is
`AUDIT.json`.

The result is construction-only and does not qualify the V19 session for live
use. It preserves `input_admission` and `input_release_measurement` as different
source event types and makes no claim of application input consumption.
