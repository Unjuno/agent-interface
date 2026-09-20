# #3851 matched-seed rank-4 minibatch RNG comparison

Status: one formal CUDA invocation completed; frozen audit returned `FAIL_AUDIT_INTEGRITY`. Do not treat the final-metric gate as valid.

This successor compares the original #3807 five seeds under two rank-4 online adapter RNG streams. It preserves the original data/base/support generation and support row order (`seed+30`); the only intended intervention is minibatch-index RNG (`seed+35` legacy vs `seed+31` shared). Each arm starts from a copied identical adapter state and runs 16 arrivals × 8 updates. The formal host is the local RTX 3080 Laptop GPU, not Docker/CI.

The exact raw stdout is retained in `raw_stdout.txt` (SHA-256 `F185E4DEAB4B19BA4B146C723CB03C1078DB53307DCBF1C2D856D9C5728C320E`); canonical payload SHA-256 is `7b2547439420aa991668cbffe29eb296a9fc4e921663e3d51053441522ce443b`. The independent frozen audit output is in `audit_stdout.txt` (SHA-256 `012AE716296C96D33C4D8A570748E46ED12EC54263F18C27CC30AF439E096708`). The five audit errors are all `curve_final_mismatch`: the snapshot helper rolls the active adapter back to its initial state and fails to restore the learned state before final scoring. Therefore the final metrics are invalid; the run is consumed, with no retries.

Pre-rollback row-level curves were captured at all 16 arrivals. A preliminary read gives legacy mean terminal accuracy 0.941895, shared mean 0.941016, paired delta -0.000879. This is not the formal disposition. CPU-only independent verification of these retained curves is assigned to successor #3865; do not retrain or revise this artifact.

The immutable allocation, H/T/D/C/U and decision gates are at https://github.com/Unjuno/agent-interface/issues/3851. Frozen source hashes were posted there; source commit `4a34a5759f1aca4dbd5495f2f46d3607df53d9d9` is on branch `research/issue-3851-minibatch-rng-local-20260921`.
