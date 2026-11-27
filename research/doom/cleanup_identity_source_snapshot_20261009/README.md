# Frozen cleanup identity source snapshots

These two files are byte-for-byte copies of the source and test blobs referenced by the frozen A02–A05 manifests. They were read from PR #8687 head `6195600931fa6de4ecf1a5012cb83b549addb5af` and stored under distinct names so they cannot replace current-main implementation files.

`SOURCE_SNAPSHOT.json` records original paths, Git blob IDs, byte lengths, and SHA-256 digests. The A02–A05 packets and their own manifests were copied byte-for-byte from that same head. A read-only hash pass checked every manifest member against the retained packet or this source snapshot; it did not run any candidate, auditor, or test. Do not treat these files as current implementation or as new scientific evidence.
