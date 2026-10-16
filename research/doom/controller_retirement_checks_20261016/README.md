# MAP01 controller: preserve session input-retirement failure

2026-10-16. Base `6a313d461ca5e9dc5e0667b881698b379351d440`.
Runtime repair `828f6ffbec27a8a26e403b57bcca97805d0ab9a0`; full affected checks
at `3272e906e31207a6c32a4e62915e510770252b9c`; POSIX test precondition repair
and dependent checks at `2f4b43b3b6a79480b3159a9f29823e31dd1b1224`.
The latter commits do not change the reviewed runtime implementation.

## Missing connection and repair

The session's #8963 retirement refusal emits `control_boundary_failed` before
terminating. V39's wait previously ignored that row until a requested predicate,
EOF or timeout. The cleanup classifier also ignored it: a retained failure plus
synthetic score/neutral-owner artifacts and no accepted intents could produce
`cleanup_complete=true` and `input_releases_verified_empty=true`.

The actual wait now rejects that failure before monitor/predicate handling, with
a `SessionControlBoundaryFailure` carrying a separate copy of its event. Even an
incomplete failure payload stops; missing obligation fields do not prove neutral
input. Consumed-event history still retains the row. Ordinary score events keep
their existing behavior.

After reader retirement, cleanup copies all observed boundary failures into its
receipt, marks task effect unknown, and vetoes release/cleanup certification.
A later score row or neutral-looking owner artifact cannot erase the refusal.
The original controller exception continues through cleanup.

## Executed controls

- Six focused methods cover failure before score/predicate/monitor, copied
  obligation, incomplete payload, ordinary score, contradictory cleanup evidence
  and actual stdout/stdin with a separate owned Python peer.
- The peer emits the failure, waits for cleanup's finish request, emits a
  deliberately synthetic score and exits zero. The actual extracted V39 reader
  and wait carry that JSONL over real pipes. The final receipt preserves failure,
  observes the later score, records reader retirement/peer exit, and remains
  unverified/incomplete. All peer streams and the reader are retired.
- The pinned-base control uses the exact old controller/cleanup files with the
  final six-method test. It has four assertion failures plus one TimeoutError;
  stdout retains the erroneous cleanup-complete/verified-empty classification.
  The first shorter five-method RED had three failures plus one TimeoutError.
  All first outcomes remain retained.
- Final normal and optimized affected checks each pass **56 modules, 413 methods,
  12 explicit skips (401 executed)**. Their source is the clean `3272e906e3` head.
  An initial full run found a missing sparse-checkout saved fixture and an old
  AST wait fixture missing the new real guard global. The original Git fixture
  was materialized, and the old test's namespace was repaired without weakening
  its assertions. Initial summaries/failed logs and focused repairs are retained.
- The four additional cleanup/pipe modules together pass **35 methods, three
  explicit skips (32 executed)** in each mode. Their first runs had two Windows errors:
  two old tests called the intentionally POSIX-only finish helper without a
  platform guard. The class now states that existing POSIX precondition. No
  Windows bounded-finish implementation or POSIX execution is claimed.

The real-pipe test uses a small cooperative protocol peer and a test finish-send
callback, not the platform-specific bounded-send implementation. The actual
reader/wait functions are extracted from main via AST; engine setup, the complete
controller main and a real game/provider are not run. Score/owner artifacts in
these controls are synthetic contradictions, never independent task scoring.

`MANIFEST.json` binds source hashes and retained outputs. `normal`/`optimized`
contain final full module logs; `intermediate-*` retain the first summaries and
failed modules. Other first-run passing logs remain in the external local output
directory instead of duplicating them in this packet.

## Remaining gates

This connects the current session refusal to its selected caller and failure
classification. Delivery failure before an event reaches the controller still
requires inspection of the session's saved failure artifact; this code does not
claim to reconstruct undelivered events. It does not add a physical release,
native-I/O/cleanup time bound, cross-backend/process authority, verified recovery,
independent live task effect or matched efficiency. No GUI/game/provider/WSL or
container allocation was used. The parent #59 objective remains active.
