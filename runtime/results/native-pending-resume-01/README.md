# Real pending response followed by digest-bound read-only resume

One primary-assistant private WSL Inkscape run, seed991115. Before allocation,
PLAN fixed timeout0 to exercise pending, without restarting if a reply won the
race. The assistant viewed the rectangle and submitted one final action: click
edge600/378, wait50ms,18 Right chords, wait50ms, save, finish_after=true.

The first response was pending with a committed digest. The assistant supplied
that run/stage/digest with resume=true and no decision. The reply contained
successful saved-file scoring, matched feedback, completed tracked cleanup and
the final image showing x86/y50/40×30. The public task requires rightward movement
and preserved geometry, not exactly x86. Owner exec12747 returned0.

One request, one compiled program, one action and43 emitted input operations
are retained. The request SHA256 and Windows UTC modification ticks were equal
before/after resume. All tracked releases were verified empty. `audit.py` checks
the saved SVG independently, source/request/reply identity, hashes and image
links without importing controller code. The manifest covers35 original files;
client response metadata and this auditor are separately Git-tracked.

This establishes real pending→reply collection for this successful local action.
The application was already finished by the later read. It does not establish
crash recovery, distributed exactly-once delivery, concurrent-controller safety,
normal application shutdown, all-descendant termination, token savings or lower
latency. Timeout0 intentionally adds a model/tool round trip; use normal bounded
waits when immediate feedback is desired. Outer delay includes host calls and
assistant deliberation, not an isolated measure of runtime speed.

No new sensor, helper model or Docker restart. Original request and reply bytes
are preserved; no input was replayed. Source commit is recorded in provenance.
