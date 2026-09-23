# ROADMAP — ACTUATION-EFFECT-RECEIPT-AUTHENTICITY-20260918-001

## H
Actuation binding fields are forgeable if effect receipts are not independently authenticated. A distinct scorer key plus exact signed effect fields and nonce freshness should eliminate forged/replayed SELF evidence while preserving valid self effects.

## T
- fixed actuation receipt and #1283 join semantics;
- independent scorer HMAC-SHA256 over effect receipt;
- candidate and separately structured oracle;
- unauthenticated bound comparator;
- excluded construction before source freeze;
- formal 5 immutable batches x66,000 =330,000 traces, 11 balanced families.

## D
PASS iff mismatch0; forged authenticated SELF0; replay re-admission0; valid signed self exact; signed external/conflict not self; malformed/no-effect exact; unauthenticated false-self>0; authority promotions0; integrity/audit pass.

## C
Scorer-key compromise defeats this mechanism. Live scorer isolation is not proven here.

## U
Standard-library synthetic receipt-authentication contract only.

## STOP
One source-first batched result, no rerun/tuning/live transfer.
