# Session-bound A03 envelope guard — result

The prior #7544 v2 wrapper was based on A01 and preserved A01's stronger `TEMPORALLY_UNIQUE` label. After the scorer-attribution parent advanced, A03 changed that contract: timestamp ties are unresolved and strict coverage yields only `SINGLE_POSSIBLE_INTENT_ENVELOPE`, never a unique intent or confirmed hold. The prior v2 files and result remain unchanged as historical evidence.

This A03-compatible successor applies the same session-identity guard before A03. On fixed cross-session rows, unguarded A03 returns `SINGLE_POSSIBLE_INTENT_ENVELOPE` with a possible token from `run-a`; the guard rejects the mismatch. Same-session strict coverage retains A03's possible-envelope status and no unique token; a release endpoint tie remains unresolved; missing identity is rejected.

Verification: v3 regression suite 4/4 PASS; parent A03 suite 13/13 PASS; parent saved-result audit PASS; v3 runner reports `PASS_SESSION_BOUND_A03`. This is local synthetic construction only. The ID is caller-supplied and not authenticated, clock identity is not bound, and no actual logs were shown to be mixed. No live task effect, recovery, safety, survival, or MAP01 result is established. Docker image-store access failed and the #59 live lane remains unassigned.
