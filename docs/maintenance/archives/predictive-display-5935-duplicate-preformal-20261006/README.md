# #5935 duplicate preformal metadata archive

This archive preserves the four metadata files from remote branch
`research/predictive-display-t0-5935-20261006-v1`, tip
`b4e108c52497018f5722f2e9b96feed3d9b9ded7`. Each file is copied byte-for-byte;
`original-commits.patch` records the branch's four commits relative to its
merge base `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028`.

The Issue's 2026-10-06 correction says this was a duplicate check with zero
formal rows. Accordingly, `FREEZE.json`'s `formal_rows: 24` is retained as
historical preformal metadata and must not be read as an executed sample. The
freeze lists hashes for `study.py`, `audit.py`, and `test_contract.py`, but none
of those files exists in the branch tree. This archive is not an experiment
package or result. The canonical 2026-10-01 T0 result is recorded separately
in [Issue #5935](https://github.com/Unjuno/agent-interface/issues/5935#issuecomment-5928484527);
the duplicate-check correction is [here](https://github.com/Unjuno/agent-interface/issues/5935#issuecomment-6015047863).

| File | Original Git blob | SHA-256 |
|---|---|---|
| `ENVIRONMENT.json` | `b5be2f4635588ac6614e7b7ce13a12412a123fe2` | `496418fb318bf2e256c0890c3f519c0dc12f9cd46425e81533042a2f4e8387f9` |
| `FREEZE.json` | `19df321002b85f28c8c4b7076a5a2513720fc076` | `4cb7219b56ca3e38e98340571e60f3fc4bb93430b62d31c5ee47f2cf1d1e4692` |
| `INPUT.json` | `7d2632efabb2166231ccaed4ae79c4876cdde531` | `1b15569c39a9ca128a996be4be9128340e8f2010fb1aa29b4b30018d5f262a0e` |
| `PLAN.md` | `3665d598eefaf50e60bed98f2eff9161260ff207` | `a1b96e7ad5e67d159e298e977cd1bc8e261c083d6a82ceca3783d0a6a86c58f4` |

The original branch ref can be retired only after this archive is merged and
the remote tip is rechecked against the SHA above.
