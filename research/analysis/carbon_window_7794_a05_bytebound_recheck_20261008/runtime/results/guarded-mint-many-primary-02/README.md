# Primary bounded-reference registration: six-task completion

Seed 991335; Linux/X11 display :147, Chromium native window 6291459. All task
input used the real SDK public MCP relay and the portable archive built from
9a080c516b6c4a7318523a51c6075cea4253b9f2 (SHA-256
5cfd7bed8fb0e32afcef6ae785d5e28f29e263813a979d5502d8ccd94b2d4f2a).
The relay included the allowlist repair in 9cde8b6b2. Workspace checkpoint was
d76a879b4. No helper model, input queue, automatic target selection, or input replay.
Host callbacks forwarded full returned text and images unchanged to the primary agent.

Independent oracle: six correct submissions, exactly once each; no missing,
duplicate, or unexpected records. Layouts A/A/A/B/B/B. All entered values were
visually reviewed before their separate Save request. The predeclared stale-reference
control on task 4 refused before input with full guard details. Two new references
were then grounded explicitly in that returned layout-B image.

30 MCP calls: one observation, two batch registrations (3 + 2 explicit references),
22 completed input programs, one refused input, three read-only retained-result
requests, and one close. Registration uses the same single-image source for each
batch and does not perform input. Close verified no held keys/buttons. Retained
registration reports were read before and after close without invoking registration.
The transport and fixture exited 0. Tracked GUI children were terminal with return
codes 0/1/1; this is not a claim that every child exited successfully.

This establishes usability for this six-task fixture. Grouping five individual
registrations into two calls saves three registration round trips by construction;
it is not a matched overall latency, token, cost, or human-tempo result. The prior
interrupted seed-991334 allocation remains in ../guarded-mint-many-interrupted-01
and must not be pooled as success or replaced by this trial. Partial batch failure
is covered by contract tests, not exercised in this successful live allocation.

Run `python -O verify.py` for archive identities, request/result matching, exact-once
submissions, review-before-Save ordering, unchanged image delivery, guard detail,
input release, batch source identities, and read-only result retrieval. The archive
also includes complete local check logs (251 protocol + 106 harness tests passed).
