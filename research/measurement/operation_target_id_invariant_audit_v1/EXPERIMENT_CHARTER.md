# OPERATION-TARGET-ID-INVARIANT-REPRESENTATION-AUDIT-20260918-001

BASE: `6685c8dd55437faf137dddeec33e30628713eafd`
Parent: #1133 / merged PR #1164

## H
#1133's full caller-visible packets have no exact-byte label collisions, but some uniqueness may come only from opaque observation/target identifiers. If those opaque IDs are treated as identity/provenance rather than semantic features, an ID-invariant structural signature will alias states requiring materially different acceptable disposition sets. If so, the corpus is valid as a data contract but insufficient as a stable backend input representation.

## T
Regenerate the exact #1133 96-row corpus from the frozen generator/seed and verify semantic digest `ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd` before analysis.

Compare one representation factor only:
- `FULL_OPAQUE`: exact canonical JSON of candidate_input.
- `ID_INVARIANT`: keep intent_id, state_epoch, binding_id, allowed_operations, payload_ref_present, and the ordered multiset of candidate `{role,ops}`; strip observation_id and candidate target IDs. No oracle/hidden/future field is added.

For each signature, collect the independent acceptable disposition set after normalizing target IDs to positional target slots so arbitrary target names cannot hide/induce a collision. Report groups whose same representation requires >1 distinct normalized acceptable set. Also run deterministic corruption controls for fabricated labels and source digest mismatch.

Construction uses 2 excluded units only. Primary is one deterministic replay over the exact 96 rows. Reruns/tuning0.

## D
`PASS_ID_INVARIANT_REPRESENTATION_SUFFICIENT_SCOPED` only if the full #1133 digest reproduces and ID_INVARIANT has zero conflicting groups.

`HOLD_ID_INVARIANT_REPRESENTATION_ALIAS` if full opaque signatures remain collision-free but ID_INVARIANT exposes >=1 group with materially different acceptable sets. This blocks a shadow backend on the current structural representation; next work must add an independently justified caller-visible semantic discriminator rather than training a larger model or memorizing opaque IDs.

Any failure to reproduce #1133 source/digest is `FAIL_INTEGRITY`; any hidden/oracle field in the representation is `FAIL_LEAKAGE`.

## C
Some opaque identifiers can legitimately carry session/currentness scope even if they are not semantic decision features. This audit intentionally asks whether the backend can generalize without memorizing those IDs. A HOLD does not invalidate the corpus contract or prove which missing semantic feature is best.

## U / stop
Container-only retained/generated evidence. No model/training/GUI/provider/task input/shared runtime. Stop after one representation audit. Do not repair the representation in the same allocation.
