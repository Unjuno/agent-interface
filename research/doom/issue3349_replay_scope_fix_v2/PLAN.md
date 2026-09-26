# Issue #3349 — replay identity corrective implementation v2

## H
Keep retained-event replay opt-in for exact terminal cleanup, and move submit response identity correlation into the wait predicate. A stale accepted/rejected row for another program must not abort a valid later response for the requested identifier.

## T
Current-main v3 full-runner candidate blob `ec16c9bbb72e02662f31d195cb3bfc9339af5c19` is copied additively and changed at one predicate only. Corrected runner blob after publication is recorded by Git. Nine deterministic protocol cases compare old and corrected submit semantics plus terminal replay. Independent audit consumes only RAW.json. No ViZDoom, X11, model, network experiment, task input, or MAP01 formal lease.

Cases: matching accept; stale accept then match; stale reject then match; unrelated then match; matching reject; malformed then match; exact terminal; duplicate terminal; wrong-ID terminal.

## D
PASS_REPLAY_IDENTITY_CORRECTION_SCOPED iff old semantics reproduce both stale-response interruptions, corrected semantics return the matching fallback in both, ordinary matching rejection remains fail-closed, exact terminal replay succeeds, duplicate/wrong-ID terminal replay fails closed, all nine cases reconcile and independent audit errors=[].

## C
This is a protocol/harness correction only. It does not establish MAP01 recovery efficacy, input-bound validity, useful task effect, or model value.

## U
The #3243 -06 BOUNDED_RECOVERY input-bound failures remain a separate downstream boundary. A future live allocation requires a fresh allocation identity and #60 coordination.
