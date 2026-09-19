# ROADMAP — MUTATION-ACTOR-RECEIPT-KEY-EPOCH-20260918-001

H: a valid MAC under a retired key must not remain SELF evidence after runtime key rotation; binding SELF receipts to runtime current key_epoch and active key closes that replay class while preserving current receipts.
T: independent per-case lifecycle traces; candidate and separate oracle; excluded fixed controls; source-first freeze; 5 immutable formal batches x48,000 =240,000 traces.
D: mismatch0; retired/future/wrong-key/altered/replay SELF admissions0; valid current SELF admitted; same nonce across distinct epochs accepted only with separately valid signatures; external/conflict/no-mutation exact; authority/task-success0.
C: current-key compromise is not solved; multi-host key distribution is outside scope.
U: standard-library synthetic lifecycle only.
STOP: no batch rerun/replacement; incomplete batch stops allocation.
