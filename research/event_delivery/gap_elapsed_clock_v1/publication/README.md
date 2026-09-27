# Publication transport

This subdirectory carries the exact original addition-only research patch in two fragments.

1. Concatenate `original_addition_only.patch.part01` and `original_addition_only.patch.part02` in that order.
2. Verify SHA-256 `3eebe00328aab0f7d6abfb1ab6c6f41b0795abdc09de2d92e2185a4fd8b4fb75`.
3. The reconstructed patch contains 450 additive files and no modifications/deletions.
4. The original local validation applied it to an empty directory and byte-compared all 450 files. It was not a live-main checkout test.
5. See `../PUBLICATION_NOTE.md` for chronology, exact part hashes and scope.

Selected source/result/audit files are expanded one level up for review convenience. They duplicate bytes already present in the patch.
