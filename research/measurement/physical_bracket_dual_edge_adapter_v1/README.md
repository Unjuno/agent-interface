# Physical bracket to dual-edge actuation adapter v1

Issue: #996  
Task: `PHYSICAL-BRACKET-TO-DUAL-EDGE-ACTUATION-20260917-001`  
BASE: `acb2d750dc6d49fdef550bf46b28f210c66ae1ce`

Decision: **PASS_PHYSICAL_BRACKET_DUAL_EDGE_ADAPTER_SCOPED**

## H

A physical-down bracket and a physical-up bracket may become one #981-style dual-edge actuation only when both parent receipts are confirmed, exact lineage matches on `{actuation_id, owner_id, intent_token, key}`, each interval is valid, and the independently censored edges satisfy `down_lo <= down_hi <= up_lo <= up_hi`.

No-op/unconfirmed/preexisting/mismatch parent evidence produces no actuation. If independent censored brackets overlap (`down_hi > up_lo`), the adapter returns `EDGE_ORDER_AMBIGUOUS` rather than inventing a correlation between the hidden exact edges.

## T

Pure standard-library candidate plus a separately implemented oracle. The construction exhausts parent status combinations, exact/mismatched lineage and separated/touching/overlapping interval shapes, then runs 250,000 seeded random pairs.

## D / result

- exhaustive cases160, candidate/oracle mismatches0;
- fixed controls15/15;
- random cases250,000, candidate/oracle mismatches0;
- false actuations0;
- random composed6,468;
- overlap rejected4,078;
- incomplete evidence202,082;
- lineage mismatch37,372;
- digest `0f43e44522e79436af2c71e09dfaf11fe6ae7580ea2e16af2b7c5e937c898db9`.

Container diagnostics: wall8.02s, max RSS93,092KB; no performance claim.

SHA-256 before publication:
- adapter `15b60121a384ef9aebacdf7392c2ee28a4637c0b5fb6016bd1f55c576e4b206d`;
- independent test/oracle `a54d9a86ee4a122ee0b152990d7f81f9e925384580aab3336a73571065f0ac27`;
- result `99bb6fbeb743342bf0cf3583fb470ec6aa0f3d9cbffb64170cc9b57be425a5bc`.

## Interpretation

Together with #992/#994, this closes the synthetic transport boundary from confirmed physical edge brackets to the dual-edge actuation expected by #981. With #988/#974, the synthetic measurement chain can conservatively represent physical occupancy and effect-time ambiguity without laundering incomplete/no-op evidence into precise useful-control claims.

This remains measurement semantics only. Actual owner-thread X11 sampling, scheduler overhead, external actors, application consumption and MAP01 usefulness require separate live/instrumentation evidence.
