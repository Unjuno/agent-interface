# Evidence delivery validation

All nine part Git object IDs were independently computed from local bytes and
matched the GitHub create_blob receipts. PACK.json binds every part and the
complete compressed/uncompressed archive. The original evidence set is 157
regular files, 3,029,116 bytes; archive 46,468 bytes.

A fresh local restoration to /mnt/data/cache_restored_review completed. The
unchanged raw-only audit reproduced AUDIT.json byte-for-byte (566 bytes,
SHA256 b5d72e691b8a9d77ca0de592a7c0adb9ab1c416e2af6fabb0d5ab3a4b89ebda3).
All four unittest methods passed again from that restored directory. No formal
allocation was rerun. The original construction metadata AttributeError and
draft freeze are retained in the archive, not rewritten.

This validates evidence transfer and scoped local tests, not repository CI,
external human review, an attested container image, or production promotion.
Exact-head GitHub checks and the integration disposition are recorded in PR/Issue
comments so this pre-PR record does not anticipate their outcome.
