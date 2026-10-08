# WSLc neutral-ID probe closeout

**Disposition:** `HOLD_SHARED_WSLc_ATTRIBUTION_AND_EXCLUSIVE_ALLOCATION_UNRESOLVED`.
**Proposed allocation:** `CGCG-6645-T1B-WSLC-REVALIDATION-20261003-01`.
**Formal WSLc candidate/auditor/retries:** 0/0/0.

The #5085 latest applicable coordination clarification preserves unresolved shared-state attribution and requires owner, host, session, allocation, duration and release to be reconciled. The 2026-10-03 read of #5085 did not reveal a release for this allocation. Later capacity and cleanup comments are observations, not a lease. See [coordination clarification](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5960813110) and [latest read-side-effect record](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5967579006).

Two earlier environment-only preflights preceded HOLD recognition; commands/outputs are disclosed in results/PREFLIGHT.md. They do not execute the candidate and do not prove absence of shared bridge effects. No WSLc command follows recognition of the HOLD.

Prepared input identities: candidate.py cfd64f422302d85ccaeb4798a5ba720a87187b3c497c375bdd1287f3c7357c3a; neutral fixture 14d26e3271f12ddff7459cdb2bb451bac20d8a698a335b64b955f80802b8a5b1; contract d526a9eba016d9f5d8d8299f75257654675ccae74c365d00a6fb656bbdf7176c. Proposal preparation is not execution authority.

This is a retained closeout, not permission to restart. Any future authorized candidate run requires a fresh allocation and current runtime receipt; preserve this STOP and parent evidence unchanged. A timeout of capture_run.py kills its local child only, does not establish container exit, and must not lead to a retry or invented release.

Separate host allocation CGCG-6645-T1B-HOST-RAW-AUDIT-20261003-01 completed read-only revalidation; it does not clear WSLc HOLD or demonstrate label invariance.
