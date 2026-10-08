# T3 first outcome — STOP_MAIN_ADVANCED_BEFORE_CANDIDATE

Allocation `LOGICAL-TIME-SYMMETRY-7327-FIXED-OVERHEAD-T3-20261004-01` was frozen and preregistered on Issue #7327 comment 5975589570 against main `d908d8f9712139f1e88a605437442a97587cbe9c`.

Before any candidate invocation, a fresh `git ls-remote origin refs/heads/main` read returned `76fe1eb1f495f8ae31e44f19f66cbf2e740583b3`. The preregistered current-main gate therefore stopped this allocation.

Disposition: `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`. Candidate=0; auditor=0; retries=0. No scientific result is claimed. The frozen spec/candidate/auditor hashes remain unchanged. Any continuation must use a fresh allocation and additive path.
