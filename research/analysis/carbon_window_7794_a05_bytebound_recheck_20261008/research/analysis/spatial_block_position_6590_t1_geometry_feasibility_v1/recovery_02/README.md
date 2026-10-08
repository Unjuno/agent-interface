# Recovery successor 02 — corrected OrbStack runner

Allocation 01 is preserved unchanged with a pre-candidate runner STOP at `../results/preflight-01/STOP.json`; no container or candidate/auditor process started there. This separate one-shot successor fixes only the wrapper's freeze-schema lookup, statically tests its exact Docker argument construction, and uses distinct container names and `results/replication-02/`. The candidate and auditor source files are the same frozen parent files; this is not a retry of launched data or a modification of allocation 01.

The previously observed host enumeration remains known. Recovery 02 tests byte-for-byte OrbStack reproduction and independent raw-only reconstruction, with zero model fits. It is not a blind confirmation or a visual-model result.
