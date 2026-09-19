# ROADMAP — MUTATION-ACTOR-RECEIPT-CURRENT-KEY-COMPROMISE-20260918-001

## H
If an adversary has the current active HMAC key, a receipt-only verifier that preserves legitimate current SELF acceptance cannot distinguish trusted-runtime provenance from compromised-signer provenance when verifier-visible receipt bytes and runtime verification state are identical.

## T
- candidate: frozen single-root current-epoch/key/nonce/lineage/MAC verifier;
- oracle: hidden producer provenance plus receipt validity;
- paired scenarios use byte-identical valid receipt bytes under fresh verifier state, once tagged TRUSTED_RUNTIME and once COMPROMISED_ACTOR;
- wrong-key and retired-epoch controls reject;
- excluded construction only before freeze;
- formal: 4 immutable batches x 50,000 pairs = 200,000 pairs;
- no repair mechanism in this allocation.

## D
PASS_SINGLE_ROOT_COMPROMISE_INSUFFICIENT_SCOPED iff legitimate acceptance=100%, compromised-forge acceptance=100%, visible-pair byte equality=100%, wrong-key rejection=100%, retired-epoch rejection=100%, authority/task-success promotions=0, integrity/audit pass.

## C
This is conditional on current-key compromise; it does not estimate compromise probability. Independent roots or protected key custody are successors.

## U
Synthetic standard-library cryptographic boundary only; no GUI/X11/model/network/task input/live authority.

## STOP
One source-first batched result. No repair mechanism, rerun, or tuning.
