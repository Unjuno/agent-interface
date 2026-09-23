# Native exchange transfer to Inkscape

2026-09-20. The existing Calc self-use harness now accepts --app inkscape while
keeping Calc as default. Setup and independent scoring use the existing gui_suite;
input still uses the same guarded native bridge, agent_exchange --native, bounded
waiting and compact image review. No Inkscape automation API or file mutation is
used to choose or execute the controller action.

## Three actual primary-assistant attempts

1. Uppercase RIGHT was rejected during native preflight as an unmapped keysym.
   Backend emissions were zero; the correlated failure report preserved the
   rejection and verified release. No automatic input retry.
2. Using the supported Right keysym reached focus, but refocusing the top-level
   window replaced Inkscape's existing child focus. The next guard returned
   SCOPE_MISMATCH. Focus completed; pointer/keyboard emissions were zero and
   release was verified. This was not an effect-free call: focus changed.
3. With child focus preserved, the primary assistant grounded the visible red
   rectangle corner at (600,378), clicked, submitted 18 Right chords and Ctrl+s,
   then viewed the returned saved-state image (source 7) before explicit finish.
   Independent SVG evaluation found x=84, y=50, width=40, height=30, transform=None
   from initial x=50. One native program completed with verified release. The
   local combined call took 908.744 ms, excluding host/model time; not a speedup.

The existing scorer requires rightward movement while preserving y and size;
it does not require exact motor gain. Eighteen chords produced +34 SVG units.
This does not establish exact key delivery, requested pixel displacement, drag
precision, or equivalence to gui_suite's separate scripted drag controller.
Keyboard nudge was the primary assistant's action choice. The observed amount
and all failed attempts are retained, not upgraded into a precision result.

## Shared fix

Guarded focus now validates the current handle and confirms actual X11 ancestry
(up to 64 links, cycle/error/unknown => refusal), then preserves that focus rather
than assigning the top-level window again. Exact child focus ID remains in the
observation and handle binding; a different ID still fails ordinary revalidation.
Window review and title-cue feedback accept a stable descendant while retaining
the registered top-level target. They do not equate windows by title/PID or grant
input authority. Review still revokes aliases; unverified release remains blocked.
No atomic capture-to-input or reparenting-race guarantee is claimed.

## Evidence and limits

38 focused tests cover the bridge, exchange, presentation and reference path.
Thirteen observation/artifact hash links across all three runs were checked.
The successful saved SVG was independently parsed after explicit finish. Tracked
processes have terminal return codes; app -15 is intentional teardown, not a
clean application-exit proof. Primary-model usage is unavailable; helper calls 0.

run-1..3 preserve raw images, programs, replies and output files. run-3/client-1
contains actual returned metadata (base64 omitted). final-source holds final
code/tests; pre-fix-bridge.py is the bridge from the base commit. Earlier harness
source was not separately snapshotted. An initial pre-setup import failure after
sparse checkout is in the conversation; restoring real_apps_v1 Python sources
resolved it. No application or input started in that import attempt.

This is one second-app transfer using a real GTK app. It is not a long mixed-app
session, a general desktop success rate or a new formal golden allocation.
SHA256.json covers retained files except this README. Base:
49084ab581b62b4e6a3c270b11c23469f56e80e8.
