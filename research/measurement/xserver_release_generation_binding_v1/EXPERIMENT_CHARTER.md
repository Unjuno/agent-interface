# XSERVER-RELEASE-CONFIRMATION-GENERATION-20260918-001

## H
After a release becomes `UNCONFIRMED_BACKEND_LOST` in X-server generation G1, evidence observed only from a later X-server generation G2 must never retroactively upgrade the G1 cleanup to `RELEASE_CONFIRMED`. A release may be confirmed only by evidence explicitly bound to the same server generation and cleanup attempt lineage.

## T
Disposable standard-library container only. Compare one factor:
- `UNBOUND`: accepts a later `key_up=true` observation for the same owner/key as confirmation even if server generation differs.
- `GENERATION_BOUND`: requires exact `{owner_id,intent_token,key,server_generation,cleanup_attempt_id}` lineage before confirmation.

Fixed traces cover same-generation confirmation, backend loss with no later evidence, backend loss followed by new-generation key-up, wrong owner/intent/key, wrong cleanup attempt, missing generation, duplicate terminal evidence, and same-generation negative key state. Then 250,000 seeded randomized traces. Candidate and separately structured oracle are compared on every transition.

## D
`PASS_RELEASE_CONFIRMATION_GENERATION_BINDING_SCOPED` iff candidate/oracle agree on every transition; zero cross-generation or missing-generation upgrades occur; same-generation valid confirmation is preserved; duplicate/foreign evidence cannot change a terminal receipt; no output grants authority/task input; malformed events fail closed.

Any cross-generation upgrade is `FAIL_RETRO_CONFIRMATION_ESCAPE`; any valid same-generation confirmation rejected is `FAIL_OVERINVALIDATION`; candidate/oracle mismatch is `FAIL_CONTRACT_SEMANTICS`.

## C
This is synthetic receipt-lifecycle evidence. It does not prove real X-server restart behavior, physical-device cleanup, host-crash safety, or production token derivation. #902 separately studies server-lifetime binding for typed UI recovery identity.

## U / stop
One construction-only state-machine block plus independent audit. No X11/GUI/model/provider/network/task input/shared runtime. Stop after first outcome; a PASS may justify a separately leased live restart/reconnect integration test, not production promotion.
