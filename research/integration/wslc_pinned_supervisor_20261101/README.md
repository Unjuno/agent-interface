# Experimental preconnected cancellation supervisor

The preceding `wslc_stale_supervisor_auth_swap_20261101` experiment showed
that a supervisor which reopens an authority path and display name can send
an old release to a replacement X server. In that version, the XRes check and
the release also used separate connections. This candidate opens one X11 backend
in the supervisor before readiness, then uses that same connection for XRes,
release and readback. It is enabled for the default X11 worker with explicit
`xauthority`; existing unpinned and custom-worker paths are unchanged.

On 2026-11-01, one fixed-order WSLc pair deliberately retired the original
private Xvfb, reused its display number, held `b` on the replacement, and sent
a **synthetic** old release obligation. With either the old authority retained
or replaced with the new authority, the preconnected supervisor reported
`xres_query_failed` and the fresh key remained down. Fixture cleanup and a
fresh guarded `a` task subsequently succeeded. In the prior unpinned swap arm,
the fresh target observed a release, providing the counterexample for this
specific change.

A separate WSLc trial exercised the real cancellation route on a still-existing
private display. The guarded owner pressed `a`, the test paused its action and
stopped Xvfb, cancellation retired the owner, and the test resumed Xvfb. The
preconnected supervisor observed owner disconnect, sent release and verified its
readback; an independent target observed `a` release and a later fresh guarded
task succeeded. Overall cleanup remained UNKNOWN, `release_confirmed` false,
and replay disallowed. The cancellation signal's `input_dispatched` field
describes the signal, not whether the original guarded action sent input.

An offline WSLc regression ran 62 existing cancellation-supervisor and owned
process tests successfully. These are fixed-condition, single attempts with
injected pauses, not latency estimates or general release guarantees. Raw
receipts, fixed conditions, trial code and complete source manifests are
included. The regression used the same pinned image and limits as the trials;
kernel output notes that memory was limited without swap enforcement.

**Remaining boundary:** a preconnected socket fences replacement *after it is
established*. It does not establish that the supervisor connected to the same
generation as the owner if replacement occurs before supervisor readiness, nor
does it integrate private-display retirement into the production recovery path.
The current path remains experimental and should not be promoted as a complete
generation fence. Retiring the server does not prove old queued input drained.
Custom supervisor targets do not receive the new pinned connection.

`raw.zip` excludes private authority files and private launcher commands; raw
and hexadecimal forms of all five recorded test cookies were checked against
the packaged evidence. The test source is a candidate based on main `e5925b6`
plus the earlier draft and the two changed runtime files in this PR.
