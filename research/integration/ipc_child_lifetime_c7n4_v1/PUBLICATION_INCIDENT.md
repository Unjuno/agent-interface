# Publication incident — exact-byte correction before PR

This file records publication transport history only. It is not a scientific result.

The first attempt to publish the complete additive patch used text reconstructed
through the conversation Files reader. GitHub created blob
`63d9af79a2006e05fd7f60e241c9b1412b85fdfd`, which did **not** match the
locally expected Git blob `2f4ecbd0f088f25f94b22cce00a46e44dce56e6f`.
The mismatch was detected before any pull request was opened. That branch file
was deleted in commit `ad9728e475a46cb88700ebb8a9f0565436a468d6`.
No scientific source, raw result, frozen gate, or consumed experiment was rerun
or modified.

Publication then switched to the authoritative binary evidence ZIP. GitHub
created blob `dcc4f15c1762dc5079bd53477368ba7689201b5e`, exactly matching the
locally computed Git object for the original 613219-byte ZIP. Its SHA-256 is
`2a8ab85627e313b66d9767e39a6bcec58a5abe67f2d8de80c22148bc636e4a9d`.

The directly readable `REPORT_JA.md` is convenience text and is not claimed
byte-identical to its original local file because the publication transport can
normalize text newlines. The exact original report and every other retained byte
remain inside `EVIDENCE.zip`.

This is a publication correction, not a new allocation, scientific retry, or
GitHub-corruption claim.
