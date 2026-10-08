# X11 persistent keymap refresh

Base: 1314d8d0113fcef1b72694e6ca0431b5420f74c5.

A private Xvfb changes from JP to US after the backend's connection is created.
Before the fix, dispatch completed but saved `http'//ab` instead of
`http://a_b`. before.log preserves that independent saved-file mismatch.
This reproduces the colon-to-apostrophe symptom with a known cause; it does not
establish the unrecorded history of the earlier ambient-display failure.

The backend now processes its queued MappingNotify events after an X server
barrier before preflighting programs containing keyboard operations.
python-xlib's refresh_keyboard_mapping updates its cached lookup table.
Pressed keys retain their original physical code for repeat/release across a
remap. The capability detail also now correctly describes verify refusal.

after.log passes the original case; both-directions.log passes JP-to-US and
US-to-JP. integration.log passes the ordinary 10-test private Xvfb suite.
unit-first.log retains four test-double setup errors caused by absent/noninteger
pending-event mocks. unit-after.log passes 21 tests after correcting those
doubles and adding held-key release coverage. native/result.json and logs pass.

Reproduce from repository root:
    xvfb-run -a env PYTHONPATH=. /usr/bin/python3 runtime/results/x11-keymap-refresh-01/both-directions.py

No user display is changed by this command. The script changes only its private
Xvfb keyboard layout. The backend connection does not subscribe to window event
streams; this change consumes its pending event snapshot.

Limits: refresh occurs at program preflight, not continuously during execution.
Concurrent map changes after preflight, XKB group selection, IME behavior and
arbitrary layouts remain unproven. The server barrier adds a roundtrip; no latency
or token-saving claim is made. These are programmatic native-input tests rather
than a fresh model visual self-use run.
