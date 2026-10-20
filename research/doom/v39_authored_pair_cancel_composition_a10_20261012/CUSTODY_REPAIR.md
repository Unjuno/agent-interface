# A10 package-custody repair — 2026-10-20

This addendum repairs the evidence manifest for the frozen package from PR
[#8843](https://github.com/Unjuno/agent-interface/pull/8843), head
`4a9baf2d5e362de64c73c51cbfa18a2667c5f352`. Seven of the original 19 digest
values matched CRLF-converted checkout bytes instead of the exact LF Git
blobs. The corrected `SHA256SUMS` was regenerated from the exact frozen PR
tree; all 19 original entries now match their retained Git blobs. This
addendum is included as the 20th manifest entry.

The non-executing `audit_a10.py` was run only in a temporary copy materialized
from those exact Git blobs. It returned `PASS_SCOPED`, and its recomputed JSON
matched the SHA-256 of the retained `results/audit.json`
(`32dfe241dd1f274e5f9fdd006f73075fbb113a48a4cf647be08ac9e6173f5442`). The
tracked original result, test, sources, WSLc transcript, and other raw files
were not edited. No test, candidate, reviewer, WSLc command, GUI, or OS input
was run again.

The retained A10 result remains `CONSTRUCTION_ONLY_SOURCE_COMPOSITION`: one
saved synthetic case checks cancel-write/flush before planner interruption,
rejects the stale response, and carries a synthetic empty terminal receipt.
It does not establish live input release, task effect, MAP01 success, or
bounded recovery.
