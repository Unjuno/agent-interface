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
