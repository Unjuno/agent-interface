# Authenticated reclaim evidence at the generation boundary

Task `COORD-GITHUB-RECLAIM-AUTH-20260916-009`, Issue #411.

**Decision: `PASS_AUTHENTICATED_RECLAIM_SCOPED`.**

This result keeps the structural reclaim predicate from #402 and generation fence from #396 fixed, and changes only issuer-key authentication of terminal evidence.

## Frozen mechanism

Two one-off RSA-2048 key pairs were created before freeze. Only public `(n,e)` values and signatures are retained. Private keys are not committed or retained. The standard-library verifier checks RSA PKCS#1 v1.5 / SHA-256 over canonical JSON (`sort_keys=True`, compact separators), then requires public-key role and exact `owner_id + generation + claim_id` binding before an owner `RELINQUISHED` or supervisor `TERMINATED` event can authorize reclaim.

Pre-measurement freeze commit: `453814115decf247421b1cc2af7ab832574ea76e`.

One non-measured prefreeze file-create attempt using filename `register_tampered.json` was rejected before commit by the tool safety classifier. The neutral filename `register_replay.json` was used instead. Signed bytes, replay control, gates, policy, and measured schedule were unchanged; measurement had not started.

## First outcomes

| Case | Frozen auth disposition | GitHub outcome |
|---|---|---|
| valid owner signature, exact binding | `ALLOW_RECLAIM` | B/gen2 commit `68d00591...`; old A/gen1 old-SHA write -> 409; readback B/gen2; `FENCED_STALE`; no retry |
| valid supervisor signature, exact binding | `ALLOW_RECLAIM` | C/gen2 commit `0a8266b7...`; old A/gen1 old-SHA write -> 409; readback C/gen2; `FENCED_STALE`; no retry |
| owner-labelled record signed by supervisor key | `AUTH_FAILED / HOLD_UNKNOWN` | zero writes; A/gen1/UNKNOWN retained |
| valid gen1 signature replayed onto generation-0 record bytes | `AUTH_FAILED / HOLD_UNKNOWN` | zero writes; A/gen1/UNKNOWN retained |
| structurally exact terminal record with unknown key ID | `UNKNOWN_KEY / HOLD_UNKNOWN` | zero writes; A/gen1/UNKNOWN retained |

Totals: two successful reclaim commits; zero writes in three negative-auth cases; two old-generation late attempts; two explicit GitHub file-SHA mismatch 409s; two post-reclaim readbacks; zero fresh-SHA retries by fenced writers.

The retained `verify.py` independently re-implements the RSA/SHA-256 verification shape rather than importing `policy.py`, checks that the trust file contains public material only, verifies both valid signatures, rejects all three authentication controls, and checks final register/result invariants. It is same-session checking code, not an independent-agent review.

## Scope boundary

This is not a production PKI result. It does not test secure private-key custody, key compromise, revocation, rotation, certificate chains, HSMs, process identity, real attackers, or external effect receivers. RSA PKCS#1 v1.5 is a fixture choice for a dependency-free verifier, not an algorithm recommendation.

Most importantly, this authenticates reclaim evidence only at the coordination register. Delayed external work from an old generation is safe only if every side-effect receiver also checks the generation/fence.

## Next single question

Keep authenticated evidence, reclaim binding, and generation advancement fixed; move the same generation token to a separate effect receiver. After reclaim, can the receiver reject a delayed old-generation effect even when the sender still holds otherwise valid request content? This tests end-to-end fencing rather than only coordination-register fencing.
