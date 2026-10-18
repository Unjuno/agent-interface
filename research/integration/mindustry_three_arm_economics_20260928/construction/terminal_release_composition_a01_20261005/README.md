# A01 — terminal status × release-state composition

## Result

`PASS_COMPOSED_GATES_SCOPED`. The exact source blobs from open PRs #7682 and
#7683 were composed into a disposable adapter candidate, then exercised through
80 deterministic in-memory responses. Both valid release schemas were accepted
with `status="completed"`; the other 78 cells (noncompleted/malformed status,
held or missing input state, invalid release metadata, or unknown fields) were
rejected. The independent auditor found zero mismatches, and its two mutation
controls reject an injected false acceptance and a duplicated matrix cell.

This closes only the logical conjunction between these two proposed host-side
adapter guards. The derived candidate is not on `main`; the PRs remain separate
open changes. No live producer, socket bridge, Mindustry process, physical input,
task effect, model/provider, Docker, or formal #5130 allocation was exercised.
It does not clear the named CPU-only slot/sibling-container ownership gate or
qualify the second-domain economics result.

The single matrix run on Python 3.14.5 ran from 2026-10-04T16:39:56.263595Z to
2026-10-04T16:39:56.272792Z. Candidate SHA-256 is
`fcb8d4d5dacd01a62fa7870323bf61faaa2c34629ab2e225022bc64fc6072550`; raw
SHA-256 is `149dfa9e7bb0ae52fd20e4fbf450d6858d89eb7763bccf2d1db8a48ad9a04e08`.
The pinned source Git blobs are #7682 `e3de478fc51ef8ba8beafd108c3da9a7c396ea6b`
and #7683 `52275025737d12c9a87a319eab05fa9b5ff65ce6`.

## Provenance and checks

The pre-run protocol is frozen in `PLAN.md`. `build_candidate.py` reconstructs
`candidate_adapter.py` from PR #7683 head
`1d7bb20bcde67333f58e41a24f8dce68f8561ffd` and the exact status guard at PR #7682
head `bd0ba260acf885d7b859d665571b2c3260666642`. The independent `audit.py`
reconstructs those bytes from Git objects rather than importing the builder,
checks all matrix cells, and verifies the source blob identities and hashes.

Commands from this directory:

```sh
python3 build_candidate.py
python3 run.py
python3 audit.py
python3 -m unittest test_audit_mutations.py
python3 -O -m unittest test_audit_mutations.py
python3 -m py_compile candidate_adapter.py run.py audit.py test_audit_mutations.py
```

The runner performs no network or system I/O. Its exchange function returns
fixed in-memory responses and each case uses one fresh submitter. No test result
here changes the frozen #5130 formal protocol or any earlier allocation.
