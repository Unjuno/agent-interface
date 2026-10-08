# MUTATION-ACTOR-RECEIPT-CURRENT-KEY-COMPROMISE-20260918-001

BASE: `020bb2713af7e115b29a71625326707e60118417`
Issue: #1277
Reservation branch: `research/mutation-actor-current-key-compromise-20260918-001`
Execution: disposable standard-library container only. No GUI/X11/model/provider/network/task input/shared runtime.

## H
Hold the exact #1272 current-epoch/key/nonce/lineage/mutation-digest acceptance predicate fixed. Change only the adversary model: the adversary knows the current active HMAC key. Under one shared trust root, a forged current-epoch receipt with valid MAC and otherwise valid fields is verifier-visible indistinguishable from a legitimate runtime-authored receipt. Therefore a verifier that accepts legitimate SELF must also accept compromised-key forgeries constructed within the same admitted field grammar.

## T
Generate paired cases with identical verifier-visible validity classes but hidden producer provenance:
- LEGIT_SELF: trusted runtime signs one valid current-epoch receipt.
- COMPROMISED_FORGE: adversary holding the same active key signs a different valid current-epoch receipt.
Controls: WRONG_KEY, RETIRED_EPOCH, FUTURE_EPOCH, SAME_EPOCH_NONCE_REPLAY, EXTERNAL, CONFLICT, NO_MUTATION.

Candidate sees only receipt/state fields and implements the #1272-style single-root acceptance predicate. Independent oracle also receives hidden `producer_provenance` and records whether an accepted SELF was trusted or compromised. Formal corpus: exactly four immutable batches × 50,000 legitimate/forge pairs = 200,000 pairs, plus fixed controls once. Fresh seed `127720260918001`; batch reruns/replacements/tuning 0.

## D
`PASS_SINGLE_ROOT_COMPROMISE_INSUFFICIENT_SCOPED` only if:
1. legitimate current receipts accepted 100%;
2. compromised current-key forgeries accepted 100%;
3. candidate verifier-visible decision is identical for valid legitimate and compromised receipts of the same validity class;
4. wrong-key, retired-epoch, future-epoch and same-epoch replay controls reject;
5. no authority/task-success promotion occurs;
6. independent audit/source integrity passes; formal primary batches=4, reruns=0.

If candidate claims to distinguish compromised producer provenance without an additional independent root/field, disposition is `FAIL_INTEGRITY_OR_LOGIC`.

## C
This is conditional-on-key-compromise evidence, not an estimate of compromise probability. It does not show HMAC is weak. Process isolation, hardware-backed keys, independent effect roots, signer attestation, and threshold signatures are separate successors.

## U / stop
Synthetic cryptographic receipt boundary only. Stop after one source-first batched result. Do not add a repair mechanism in this Issue.
