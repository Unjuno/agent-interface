# A01 pre-freeze construction log

These are construction-only failures before `FREEZE.json`; no formal candidate
or auditor CLI was invoked and no scientific T0 result is claimed.

1. The first `node test_construction.js` invocation rejected the candidate
   input identity because `candidate.js` omitted the date suffix present in the
   frozen-allocation label. The candidate identity check was corrected before
   freeze.
2. The next construction invocation failed the `staleAnswerDoesNotAct` gate.
   Inspection showed the version change at tick 3 occurred after the immediate
   policy's reply at tick 2, so that row was correctly still current. The
   version-change fixture was moved to tick 1, making the immediate reply
   stale, and a separate pre-delivery cancellation gate was added. This was a
   test/fixture construction correction; no frozen or formal output existed.

The later identical construction command passed with 15 requests, 45 policy
rows, one mandatory event, and five detected candidate-output mutations. The
passing construction command is not a formal allocation; formal CLI counts
remain 0/0 at freeze.
