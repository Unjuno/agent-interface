# #1433 physical-edge clock-domain gate A2

Decision: `PASS_PHYSICAL_EDGE_CLOCK_DOMAIN_GATE_A2_SCOPED`.

A2 changes only fixed-control completeness after #1002 retained a PASS-shaped first outcome with an omitted explicit reversed-interval control. Exact #996 parent semantics are pinned to adapter Git blob `a1344409ea6383c6394e991ac0b59fa7689978ef`. Parent, candidate and independent oracle source SHA-256 values are unchanged from the consumed predecessor; only the runner adds explicit reversed-down and reversed-up controls and the A2 task/decision labels.

One frozen seeded construction evaluated 250,000 pairs. Candidate/oracle mismatches were 0; same-clock parent-degeneration mismatch was 0 across 173 comparable confirmed-edge rows; 11,680 confirmed-edge rows with cross/missing clock provenance produced 0 compositions. Authority promotions and malformed oracle divergences were both zero. All 12 fixed controls passed, including explicit overlap, reversed-down and reversed-up cases. Primary1/reruns0/replacements0/tuning0.

The candidate requires nonblank exact equality of `clock_domain` and `clock_epoch` before temporal comparison. Missing provenance returns `CLOCK_PROVENANCE_MISSING`; mismatched provenance returns `CLOCK_DOMAIN_MISMATCH`. For same-clock evidence it reduces to exact #996 composition semantics. Clock metadata grants no authority.

Result SHA-256: `158fe463a98ae55b1e444659463cd0957030b7b9d96f20051aa24ecd3b6e906e`.

Limits: equality of authored clock labels proves only declared comparability. It does not synchronize real processes, bound drift, prove X11 physical timing/application consumption, or establish task/MAP01 usefulness, human tempo, or production behavior.
