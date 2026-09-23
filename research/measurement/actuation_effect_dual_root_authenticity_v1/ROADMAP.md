# ROADMAP — ACTUATION-EFFECT-DUAL-ROOT-AUTHENTICITY-20260918-001

H: Under compromise of only the scorer HMAC key, requiring valid signatures from both the scorer root and an independent application/effect root over identical effect receipt bytes eliminates scorer-only forged SELF evidence while preserving legitimate dual-signed SELF effects.
T: Freeze common canonical payload and two independent keys; candidate 2-of-2 verifier and separately structured oracle; scorer-only baseline; excluded controls; source-first freeze; formal 4 immutable batches x 60,000 = 240,000 traces across 10 families.
D: PASS iff mismatch0; dual-root false-self0; valid dual self accepted; scorer-only/mismatched/wrong-key/mutated/replay fail closed; scorer-only baseline false-self>0; authority0; integrity pass.
C: Both-root compromise or lack of operational independence defeats the mechanism; this does not establish live app key custody.
U: Standard-library synthetic two-root contract only; no GUI/X11/model/network/task input.
STOP: One source-first batched result, no rerun/tuning/live transfer.
