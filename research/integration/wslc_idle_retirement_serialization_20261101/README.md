# Idle retirement wake, serialization and cancellation overlap

This preserves an experimental sequence following
[the retired-owner stale-response comparison](../wslc_idle_retired_owner_response_20261101/).
All candidates here are local prototypes based on draft #10094 at
`e6ed07edad270cc4631518bf3b53124e4ada28b6`; none is added to main by this
packet. Main at the final trial freeze was
`faad13e775729a212c669d389a869cd00a67d33a`.

When a child was retired with its idle reply unsent, a wake-event prototype
returned the idle caller without waiting for the 2-second deadline. In one
private-Xvfb run the earlier candidate returned 1,978.786 ms after retirement
started and the wake prototype returned 0.063 ms after start, **before** the
retirement call finished. A controlled fake-process probe then showed that a
concurrent close could enter termination a second time. Those measurements are
single samples and do not establish hard latency bounds.

A subsequent local serialization candidate defers close during retirement and
returns an in-progress result for a competing retirement. In one controlled
real-child/private-Xvfb treatment, termination was deliberately paused; close
deferred, the competing request did not issue a second termination, and the
first call later retired the child. The control completed a normal observation
and close. A new owner then typed and released `a` in each arm. Old cleanup in
the retirement arm remained UNKNOWN. The old owner held no input during this
scenario. Initial r118 regression had six fixture-compatibility errors; r119
corrected that issue and passed 96 tests in normal and optimized Python.

An additional local candidate reports whether retirement was in progress **at
the cleanup attempt**, retaining UNKNOWN and no implicit replay. With a real
spawned owner and prestarted cleanup supervisor, one ordered and one overlap
trial deliberately held parent-side timeout and termination gates. The ordered
trial recorded a readback-verified supervisor attempt; overlap recorded
not-attempted and no supervisor call. Both old cleanups remained UNKNOWN. The
old owner held no input; a separate new owner performed and released `a`. The
earlier r122 candidate passed 97 selected tests in both modes, and r123 renamed
the new fields to historical wording and passed seven targeted tests in each
mode. The gates, small samples and unheld old input limit these findings; they
do not prove safe retry, general recovery, physical input or MAP01 behavior.

`raw.zip` retains candidate source, conditions, raw outcomes, the failed r118
run, and audits; `archive-manifest.json` hashes each entry. `python audit.py`
verifies archive bytes and re-runs the three saved real-X report auditors.
Host-specific `private-command.json`, Python bytecode and local red-test traces
with Windows paths are excluded; originals remain local. The saved reports
describe observed outcomes, not proof of absent unrecorded events.
