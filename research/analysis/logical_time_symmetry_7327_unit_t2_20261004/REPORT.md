# Issue #7327 UNIT T2 — scoped result

Allocation `LOGICAL-TIME-SYMMETRY-7327-UNIT-T2-20261004-01` passed the finite explicit seconds-versus-milliseconds representation gate: six distinct raw pairs, exact conversion of 48 declared time fields and seven event timestamps, six identical independently reconstructed traces, and 4/4 mutation rejections. Candidate and auditor each ran once, exit 0, no retries. Host Python 3.14.5 was used after OrbStack image inspection failed; no container-limit or runtime-speed claim.

See [the full result](RESULT.md), [frozen source identities and run receipt](RUN.json), and [pre-invocation freeze](FREEZE.json). T1's candidate/schema STOP remains preserved separately. Issue #7327 remains open; this does not establish live-control or full logical-time model validity.
