# Retrospective delivery repair

The original research branch was 33 commits ahead and 1,154 behind current `main`. Its GitHub compare contained only additive paths, but the published capsule restore failed integrity checks. A rescue branch was therefore based on current `main`; the original branch and all historical study files remain unchanged.

Two transport defects were isolated and repaired without changing study payload bytes:

- The `CAPSULE.json` encoded-text digests did not match the checked-in base64 part bytes. The metadata now records the actual bytes. Decoded-part digests and the final archive digest remain the preregistered values.
- `part-05.b64` did not match its declared decoded digest. The four retained fragments `part-05a.b64`–`part-05d.b64` concatenate to the expected 8,000-byte base64 part and decode to the declared 6,000-byte digest. `restore.py` uses and verifies those fragments.

Verification performed from a clean extraction:

- reconstructed capsule: 89,168 bytes; SHA-256 `4acdf7feec6f3bca6e1116241f37013855c96e1a80d6fed91f616ee5b5bf9dc1`;
- archive: 624 entries, no absolute/traversal paths or links;
- restored evidence files: all 624 listed file hashes match; the only omitted file is the separately pinned runtime executable;
- Actions artifact `10847727571` from run `36096442879`: runtime SHA-256 `b7490f97a01991009e72e1b03410ca244cceeabba12103549c1288ef464c5f19`;
- original read-only verifier: all five saved audit/control outputs reproduced byte-for-byte, including the expected construction audit exit 1; 1,157-check primary audit and ten corruption controls pass;
- scientific/GUI reruns: 0; retained source and evidence unchanged.

The verifier ran from a Linux-native temporary copy under WSL; running it directly from the Windows-mounted checkout exceeded its 30-second per-command limit. This delivery validation does not claim repository CI or independent human review; those remain PR gates. The scientific result remains the scoped local PASS, not a general durability or retry-safety claim.

## Exact pre-repair manifest preservation

`CAPSULE_PRE_REPAIR.json` is a byte-for-byte copy of the original branch's `CAPSULE.json` at `research/cli-report-persistence-retained-3711-20260926-p4n7`, branch head `8ffc61f8ab45e88ff52828db2ee5f390e349630c`. Its Git blob is `6edebb0c728b417331afe6df14c93002c670c769` and file SHA-256 is `ae49232fa2ce221ec379c036e4336a865e43dc2f876214ed56be0bffd4a3f745`. It is retained as historical failure evidence; the current `CAPSULE.json` remains the repaired manifest used by `restore.py`.

An independent digest check against the exact old branch bytes found all 15 original `text_sha256` declarations disagreed with their corresponding checked-in part bytes. The repaired manifest now matches the 14 direct part files; the part-05 digest is checked against the exact concatenation of `part-05a.b64` through `part-05d.b64`, which reconstructs the expected 8,000-byte base64 member. This preserves the original mismatch without changing either historical manifest or any experimental result.

On 2026-10-01, the repaired capsule was restored again from a disposable copy using `python -S -B restore.py` in `python:3.13.5-slim` (`sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, `--network none`). It emitted 89,168 bytes with SHA-256 `4acdf7feec6f3bca6e1116241f37013855c96e1a80d6fed91f616ee5b5bf9dc1`. This is a data-restoration integrity check only, not a scientific rerun.

## Exact pre-repair restorer preservation

`restore_PRE_REPAIR.py` is a byte-for-byte copy of `restore.py` from the same original branch head `8ffc61f8ab45e88ff52828db2ee5f390e349630c`. Its Git blob is `6e419cc2bfb82a4376d30c18f7f082016ff3c253`. The original program validates each encoded part against the mismatching historical `CAPSULE.json` and therefore stops on the first transport digest mismatch; it is retained as failure evidence, not used to restore the capsule. The current `restore.py` and repaired `CAPSULE.json` remain the validated reconstruction path. No original files or results were rewritten.

`README_PRE_REPAIR.md` is a byte-for-byte copy of the original branch's README. Later additive paragraphs in the active README document the transport repair, preserve the exact original manifest and restorer, and give the retained verifier-artifact reproduction instructions; the historical README snapshot intentionally contains none of those retrospective additions.
