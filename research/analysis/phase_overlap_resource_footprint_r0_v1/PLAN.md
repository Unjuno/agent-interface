# #1720 — phase-overlap resource-footprint serializability

## H
For two deterministic intents with one serialized actuator, B may begin while A's tail is pending iff every overlapping phase has complete declared read/write footprints and A-tail has no RW/WW conflict with B's phases. UNKNOWN fails closed to SERIAL. Under those assumptions the overlapped execution is observationally equivalent, on all declared resources and per-intent reads, to whole-intent serial A→B.

## T
Standard-library finite exhaustive analysis over three logical resources, binary initial states, deterministic read/write/increment/copy operations, serialized input and pending-tail phases. Candidate order is A.input → B.input → A.tail → B.tail; serial oracle is A.input → A.tail → B.input → B.tail. Exhaustively test complete footprints and negative controls: surface-only, one omitted actual A-tail write, UNKNOWN fail-open check, and reversed conflict predicate. One source-frozen formal invocation; independent gate audit and corruption controls.

## D
PASS only if complete-footprint admitted mismatch=0; every declared conflict serializes; UNKNOWN parallel admissions=0; all three negative controls expose mismatches; both serial orders are covered analytically; integrity/audit/corruption controls pass.

## C
Static footprints may be incomplete or data-dependent. Syntactic conflict is sufficient but not necessary because commuting/idempotent writes may be safe. Real event loops and hidden global state can violate the deterministic model.

## U
Analytical contract only: no GUI/X11/model/runtime mutation, no speedup or production promotion claim.
