# E01: current v39 reader-fault boundary, parent #59

Prospective diagnostic only. No repair, game/model/input startup, formal 114 replay,
or claims about live-user task success. Existing T6/PR6050 and PR7103 completion
ordering experiments are not repeated. Bounded searches of v39 JSONDecodeError,
malformed, session-reader and #59 comments found no matching focused probe;
startup missing-fixture and appserver sidecar failures are distinct.

## H/T/D/C/U

- H: a malformed JSON line kills the current nested reader while its owned peer
  remains alive; current wait surfaces only TimeoutError, not the parse failure.
- T: healthy ready, malformed `not-json`, JSON array `[]`, in that fixed order;
  one fresh stdlib peer per cell, one run only. Extract literal reader/wait AST
  from pinned main source, without altering either function. Instrument only
  threading.excepthook to retain exceptions, never feed them into the queue.
- D: FINDING_PARSE_FAILURE_NOT_SURFACED requires ready/TimeoutError/TypeError,
  live children at result checkpoint, expected reader states and parse error,
  all owned children exit 0 and readers retire. Disagreement HOLD; custody or
  cleanup failure STOP. First outcomes preserved, no repeat to obtain success.
- C: normal ready is a positive control; parsed wrong-shape JSON distinguishes
  parser failure from wait's unchecked object shape. Peer emitted-hex receipt is
  emitter provenance, NOT actual raw stdout readback. JSONDecodeError.doc is
  captured actual decoded parser input. Source/execution identities must close.
- U: wait timeout is explicitly overridden to .35 seconds (default 40 seconds
  not measured); queue floor and host scheduling preclude a hard deadline claim.
  Directed fault injection establishes a conditional mechanism, not natural
  fault frequency, full-controller adoption, physical input release or recovery.

Snapshot: main 1d7cc6465964296215a4fb546c41a313841a367c, current v39 SHA256
`a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e`.
README/CURRENT_GOAL/ROADMAP and open/closed issues/PRs/branches refreshed at intake.
D03 PR7199 integrated HOLD_NOT_SUPPORTED, not latency-policy success. Remaining
roadmap includes live task-effect/control gates; this probe cannot complete them.

Allocation E01-59-20261004-3CBF: own VM research-6183-t0-20261003 and own Engine;
CPU 1, memory/swap 512MiB/0, PIDs64, nonroot501, networknone, read-only source/root,
capdropALL, no-new-privileges. No exclusive physical-host claim.
One native producer, then one saved-only auditor after producer exit0; retries0.
Source/commands/image will be frozen and publicly read back before native launch.
