# ROADMAP — MUTATION-ACTOR-RECEIPT-AUTHENTICITY-20260918-001

## H
Trusted lineage semantics alone are forgeable if an untrusted process may self-assert THIS_INTENT. Runtime-owned HMAC-SHA256 over canonical receipt fields plus exactly-once nonce consumption should reject forged/replayed SELF receipts while preserving valid SELF and explicit external evidence.

## T
1. Freeze canonical receipt fields and key/nonce semantics.
2. Candidate: MAC admission then fixed actor classifier semantics.
3. Independent oracle: separate canonical encoder/MAC verifier + replay state.
4. Excluded controls only before source freeze.
5. Source-first publication/readback + ownership reread.
6. One formal seeded corpus >=300k rows; no rerun/tuning.
7. Independent audit from retained aggregates/source; corruption controls.

## D
PASS iff mismatch0; forged/replayed SELF0; valid SELF admitted; external exact; conflict unattributed; nonce exactly-once; malformed/unknown key fail closed; authority/task-success promotions0; audit/integrity pass.

## C
A compromised runtime key defeats this mechanism; HMAC authenticates broker receipts, not humans/kernel/process identity generally.

## U
Standard-library synthetic authenticity contract only. No GUI/X11/model/network/task input/live authority.
