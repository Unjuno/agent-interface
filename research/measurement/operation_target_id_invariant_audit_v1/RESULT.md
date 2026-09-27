# ID-invariant operation/target representation audit

Decision: **HOLD_ID_INVARIANT_REPRESENTATION_ALIAS**.

The exact merged #1133 generator reproduced parent corpus semantic digest `ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd` over96 rows.

One representation factor changed:
- FULL_OPAQUE: exact #1133 candidate_input packet.
- ID_INVARIANT: observation IDs and candidate target IDs removed from the backend semantic signature; intent/state-epoch/binding/allowed-ops/payload-presence/candidate role+compatible-op structure retained.

Results:
- primary invocation1 / reruns0;
- FULL_OPAQUE conflicting groups0;
- ID_INVARIANT conflicting groups28;
- independent audit PASS;
- copied-result mutations4/4 rejected;
- frozen source rehash all exact;
- model/GUI/task-input actions0.

Repeated conflicts include:
- `CLICK_MULTI ↔ AMBIGUOUS_TARGET`: the same two-button CLICK structure requires either two acceptable CLICK targets or YIELD(AMBIGUOUS_TARGET);
- `NO_LOCAL_ACTION ↔ MISSING_TARGET`: the same zero-candidate structure requires either NO_LOCAL_ACTION(ALREADY_SATISFIED) or YIELD(MISSING_TARGET);
- in four stale-control units, `CLICK_UNIQUE ↔ STALE_STATE`: the same one-button CLICK structure requires CLICK versus YIELD(STALE_STATE).

Scoped interpretation: #1133 remains valid corpus-contract evidence, but its current structural caller-visible representation is not sufficient for a backend that does not memorize opaque IDs. Do not allocate a larger/shadow model on this representation. Add one independently justified caller-visible semantic discriminator/family, then re-audit collisions in a fresh successor.
