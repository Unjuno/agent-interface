# Issue #4221 construction/formal plan

H: exact bound DestroyNotify sets only the current bridge's existing `review_required`; pre-review old alias refuses without input, exact `review_window` advances one revision/scope and revokes old aliases, and a fresh alias remains usable.

T: exact current-main source; private Xvfb + Openbox + same live actor. Construction is one excluded session. Formal, only after construction pass and public freeze, is four fresh sessions from the same runner, one invocation, no retries/replacements/tuning.

D: PASS_DESTROY_REVIEW_COMPOSITION_SCOPED only under Issue #4221 gates: exact DestroyNotify; same-XID/equal-pixel replacement; stale pre/post review zero effect; review revision +1/new scope; fresh effect exactly once/3 XTEST emissions; verified release and cleanup; raw-only audit and corruption controls.

C: no promoted watcher/runtime change; no active-input destruction, event-gap/reconnect, model/token/latency/public-CLI claim.

U: actual long-path integration and #2789/#3311 matched evaluation remain open.
