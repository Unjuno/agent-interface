# LIVE-EXISTING-RUNTIME-READY-FENCE-20260917-001

## H
The existing `interactive_v27` `ready` record is a natural producer-startup boundary. Waiting for that record before advertising `observation_socket` should preserve a later 300 ms EventCursor budget for an ordinary read-only `clock` event; exact v11 endpoint publication should spend that budget during startup.

## T
Use the retained offline artifact SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`. Exact `interactive_v27.py`, baseline `event_socket_v11.py`, and `session_v16.py` Git blobs are pinned. Six fresh xterm sessions, three matched seeds, counterordered policies, one formal top-level invocation, zero reruns. No task program is submitted.

## D
`PASS_EXISTING_RUNTIME_READY_FENCE_SCOPED` iff baseline endpoint receipt precedes runtime ready and its 300 ms clock read times out 3/3; candidate reaches clock boundary 3/3 and satisfies `ready emit <= ready append <= endpoint publication < initial observation <= clock`, with non-authority read results, no task-program events, neutral verified owner release, and exact source/freeze integrity.

## C
Any apparent benefit may only move startup wait outside the read budget. The natural ready event could cease to be a sufficient milestone if later runtime initialization changes.

## U
One xterm/private-X11 path, unpinned host scheduling, no model/token/task success claim. This does not promote a production ABI or second-domain transfer.
