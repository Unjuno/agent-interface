# X11 keyboard mapping between program operations

Directed engineering regression on WSL 3.0.1 / Ubuntu, kernel 6.18.40.1, Python
3.12.3, private Xvfb/Openbox and independent Tk effect/event files. This integrates
an operation-boundary guard into the production X11 backend. It is separate from
issue #5236's frozen formal allocations; their STOP_PROTOCOL_DEVIATION disposition
and historical bytes remain unchanged. No model or sensor implementation was used.

Baseline bfa0025d2f510a35c0b2d089f963b18cd52f1dd2 refreshed MappingNotify only at
preflight. Separate setxkbmap clients changed layout during a declared 111ms wait.
One fresh server/app/backend per case, identical program: focus/click, wait100,
text a, wait111/remap, text _, Ctrl+s, wait250, release. Stable US saved a_; JP->US
saved a and US->JP saved a=, all reported completed. Native effects were wrong.
The first five unit regressions had three failures on the original implementation.

The first notification-only candidate stopped even stable US. Retained read-only
snapshots show repeated MappingNotify with identical core keysyms and modifiers.
That candidate was rejected. The integrated guard snapshots core keysyms and
modifier bindings during preflight and, before keyboard operations, processes
notifications and compares the actual notified map. Real changes latch for that
program; subsequent positive keyboard input fails without replay. Explicit key-up
remains possible using the original held physical code. Identical notifications,
pointer notifications and a map already present at new-program preflight are
covered separately by six unit tests.

The source candidate and the committed portable archive both passed the directed
three-case matrix: stable saved exact a_; both remaps failed at operation7 before
underscore and Save, with executed prefix and verified release. Packaged revision
fe7ec5f6a687dd34990be441f7a977faae267782; environment.json records the actual zip
backend import path. The packaged trial additionally recorded all32 keymap bytes
and pointer masks via the private session's separate X connection: no key or
mouse button remained pressed. Cleanup records keep actual app and child exits;
terminated fixture apps are not relabeled as normal exit0.

GUI test integration had failures retained in full. An initial shared application
left prefix text, and subsequent punctuation input mismatched even after owning
a fresh app. Mapping changes affect the entire server; the final mapping test owns
a separate application lifetime after the ordinary integration fixture closes and
restores the original map with xkbcomp. One run after that separation still failed
the existing button-release readback assertion. A planned three-pair control on
ordinary10 tests reproduced that exact failure in one baseline replicate, while
all three candidate replicates passed. This is evidence of a baseline instability,
not proof that the release problem or all rendering races are solved. The first
comparison runner mixed replaced backend exception classes with an imported
session; its four baseline errors are retained but rejected as runtime evidence.
The corrected runner reloads the session alongside the replaced backend.

Final private GUI/input/artifact/CLI-boundary suite:54 tests passed. Local native
protocol324 and harness141 passed. The first broad mock tests and deadline harness
failures are retained: no-display fixtures needed an explicit stable/no-notification
read seam to continue testing their original emission and expiry boundaries.
Physical-emission, original-key release and deadline assertions remain intact.
CI includes the six new mapping tests and installs x11-xkb-utils for live remapping.

Limitations: check/send is not atomic; changes within one text/chord/state operation
and arbitrary XKB group/IME state are outside this boundary fix. Read barriers and
snapshot queries add unmeasured cost. No human-tempo, generic application accuracy,
latency, token saving, formal allocation PASS or semantic completion is claimed.
The existing conservative partial-effect receipt is retained. The failure is
visible to the caller; the interface does not silently replan or replay a suffix.

metrics.json identifies selected results; evidence.zip retains216 source, program,
actor, event, effect, cleanup, environment, failed-run and test-log files including
the exact portable artifact. manifest.json pins every archived byte. Run
`python -O runtime/results/x11-mapping-boundary-01/verify.py` for archive closure and
selected data checks. The verifier does not replay GUI operations or perform an
independent adoption audit.
