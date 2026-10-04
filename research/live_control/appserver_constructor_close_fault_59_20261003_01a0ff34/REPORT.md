# Constructor cleanup faults preserve diagnosis separately from file release

Ordinary E boundary, actual worker `01a0ff34-0b3d-7921-846a-6044960fcf76`, FINAL-v5.
Parent #59, prospective claim5969150279. This extends the explicit untested cleanup-close-fault limit of #7018; its prior first12 cells, head, vote and ownership remain unchanged.

Frozen main e74cfc78b84d286ff3faabf2696129b988655c1b has the unchanged6194B client6032c0dd1d7441977afca790d08d1f1012e8f18171691249456fcfe90097617e.
Three constructor images change no other15 method ASTs: current, naive try/close/re-raise, and protected cleanup with a class-only exception note and original bare re-raise. References are inert .py.txt archives, not adopted code.

H/T/D/C/U:18 first native-file construction cells, three images times two inert factory primary exceptions (OSError/KeyboardInterrupt) times three cooperative journal-close conditions (healthy, refusal before real close, refusal after real close). Only the journal open/fileno/fstat/TextIO close are actual OS/file operations; the factories never create a process. Driver-owned wrappers are intentionally retained to inject faults and perform final cleanup. This does not repeat the prior traceback-lifetime diagnosis or establish post-GC leakage. All failure classes, object identity, primary context, notes, native fd and TextIO states are measured before driver cleanup and persisted. Gates/source/order/caps were fixed before first execution. No cell/source/native producer replay.

| Constructor | Original primary preserved | Secondary replaces primary | Source closes actual fd |
|---|---:|---:|---:|
| Current |6/6|0/6|0/6|
| Naive close/re-raise |2/6|4/6|4/6|
| Protected close/re-raise |6/6|0/6|4/6|

The naive cleanup exception retains the primary as its implicit context, but callers receive CleanupFault rather than the original OSError/KeyboardInterrupt object. Protected paths receive the original object; both injected cleanup failures attach `journal cleanup failed: CleanupFault`. In each reference, failure before real close leaves2 native fds open, while failure after real close still leaves2 closed. A note is diagnosis, not release evidence. Current performs no cleanup in any case. All18 real files are empty and their native fds are closed by the end, using explicit driver cleanup where required. No actual human cancellation was injected.

Collector21008:2026-10-03T12:29:29.576506–29.687684UTC exit0, stdout135B/eb0bc7f804596d58b742dc19bc0abb96fc23ed598f6f8c62ec8d88205565c773, stderr0. Separate saved-only oracle33512:12:29:30.656344–30.719207UTC exit0, stdout1683B/3ebd3848da25e7eba6cea1662ffbd3348047bf56015304bc6bad441173522787, stderr0. It checks all18 exact ordered cases and rejects12 effective copied typed/state/identity/context/note/resource corruptions. Both are new ordinary construction/data-reader executions, not a formal allocation. Full commands/PIDs/UTC/exits/raw streams are retained.

First unused source transport had one extra LF (6195B/f1c2aef43a4a71fcde12697b5fa7b659d65b8a2869fe6ccde486110da4ca3b71); the pre-execution pin check found it. Original copies/freeze remain under unused-first-freeze. Explicit exact transport repair occurred before any cell; final freeze dd87cbe4512b232e0e5dbaca3509c80219817073c517c10143ae2c13f30831ef and RAW a20095516f2dd70759e84d27da367a54df5c737419d49f7b320ff2b9017964ae remain unchanged. There was no failed/omitted subject cell or postresult gate change.

Scope: native Windows CPython3.12.14, single bounded collector, cooperative injected faults and built-in primary exceptions supporting add_note. Exception subclasses overriding add_note, hostile close/error formatting, indefinite close, journal-open/thread-start faults, partial Popen internals/descendants, real provider/model/game/GUI/input, total deadlines and task/recovery/efficiency remain unqualified. No production adoption, full suite/hosted CI, shared lease, content vote, current application or main send. Prior source owners retained. This counterexample changes repair design: preserve the first failure independently and report incomplete cleanup rather than counting attempted cleanup as release.
