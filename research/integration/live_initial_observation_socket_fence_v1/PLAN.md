# LIVE-INITIAL-OBSERVATION-SOCKET-FENCE-20260917-001

## H
The existing exact `interactive_v27` initial observation event is a later natural startup boundary than `ready`. Advertising the observation socket only after EventCursor appends `{event:"observation",id:"initial",exact:true}` should preserve the unchanged 300 ms budget for a subsequent read-only `clock` event; exact v11 should spend that budget during startup.

## T
Retained artifact SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; exact pinned `interactive_v27.py`, `event_socket_v11.py`, `session_v16.py`. Six fresh xterm sessions, three matched seeds, counterorder, one case per outer container invocation, zero reruns. No task program submitted.

## D
`PASS_EXISTING_INITIAL_OBSERVATION_FENCE_SCOPED` iff exact v11 endpoint precedes initial observation and clock times out 3/3; candidate reaches clock boundary 3/3; candidate order is `initial emit <= initial append <= endpoint publication < clock emit`; no task-program events; final owner verified neutral; exact source/freeze integrity.

## C
A PASS can come entirely from moving initial-snapshot startup work outside the event-read budget. It is not a runtime speedup and may be too conservative for runtimes that can safely accept commands before first capture.

## U
One xterm/private-X11 retained artifact, unpinned host scheduling, no model/token/cross-app/production ABI claim.
