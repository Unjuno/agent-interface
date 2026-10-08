# Archival qualification: cyclic justification grounding #4431 / #4443

This is a **published-byte preservation record**, not complete evidence delivery or a new scientific result. The reported local disposition remains `PASS_LOCAL_CYCLIC_GROUNDING_CONTRACT`; the separate publication disposition remains **`HOLD_REMOTE_RAW_DELIVERY`**. The available source, proof, result and publication wrappers do not establish lossless raw recovery, independent reproducibility or runtime readiness.

## Exact published material preserved

- Owner: [Issue #4431](https://github.com/Unjuno/agent-interface/issues/4431); original [Draft PR #4443](https://github.com/Unjuno/agent-interface/pull/4443)
- Original branch: `research/cyclic-grounding-1816-20260926-t6g2`
- Exact published head: `94c187f8d7198a10a2fa6b175fb195ac093ff2ce`
- Complete original package tree: `79da8f5db84d867349656b6849715015d985041c`
- Five-file `original/` tree: `9d9440a69627e2728fa170aae7638487cb57d19a`
- Original path: `research/analysis/cyclic_justification_grounding_delivery_t6g2_v1/`

All **nine published files, 25,174 bytes**, are preserved without modification: five original files totaling **17,489 bytes** and four published wrappers totaling **7,685 bytes**. This qualification is an added file outside the immutable `original/` tree and does not replace or revise any of those nine files.

| Published path | Bytes | Git blob SHA-1 |
|---|---:|---|
| `original/PROOF.md` | 8,218 | `7e73b71d423cfbab59413c0481c190f0ff01805d` |
| `original/RESULT.json` | 1,658 | `423311963ebeb250491c82d45932a843438bc01e` |
| `original/source/corpus.py` | 1,043 | `5c9f75c1b9c1b10630a09268e5f80a6b23c08140` |
| `original/source/grounding.py` | 5,117 | `e69b9d4949420aeb0bfea22071d6e0406e1edceb` |
| `original/source/run.py` | 1,453 | `9d83407a690716551867f75606887155d552ccd6` |
| `PUBLICATION.json` | 2,680 | `a8706499642f700c2836ac781432a66d7119703b` |
| `PUBLICATION_HOLD.md` | 1,212 | `36c2160861baad7ab40bbeb22e26f696dd8cd31d` |
| `README.md` | 1,794 | `17c511c8b12c8e88635744cbcb88d63684e23f6d` |
| `verify_publication.py` | 1,999 | `1b92e2bbc16c2e3d5412e71dba21a4c1c90590c6` |

The complete, non-truncated package tree and PR file list agree on those nine files. Their retrieved bytes were checked against Git blob identities and byte lengths; the original and package tree identities were reconstructed from those objects. These checks verify preservation of published bytes, not the study's scientific conclusions.

## Missing evidence and misleading historical delivery wording

The [owner's publication update](https://github.com/Unjuno/agent-interface/issues/4431#issuecomment-5841664789), the Draft's disposition and [`PUBLICATION_HOLD.md`](PUBLICATION_HOLD.md) state that the full `RAW.jsonl` and complete retained audit/control/process bundle are not published on the original branch. This gate remains unchanged.

The preserved [`README.md`](README.md) says that `capsule_parts/` reconstructs a complete capsule and invites execution of `verify_publication.py`. That wording is a historical delivery overstatement: **no `capsule_parts/` directory, no capsule, no RAW.jsonl and no full audit/control/process bundle exist in the nine-file published package**. The README is retained byte-for-byte as evidence of that state, not endorsed as a working reconstruction procedure. `PUBLICATION.json` lists part identities; the list is metadata, not delivered part bytes. The retained verifier depends on those absent parts and would execute auditor/control scripts if its prerequisites were present. It was not run for this preservation.

These are reported unavailable-byte identities, not newly verified artifacts:

| Reported artifact | Reported bytes | Reported SHA-256 |
|---|---:|---|
| `RAW.jsonl` (the wrapper expects `evaluation/RAW.jsonl` inside its capsule) | 16,003,195 | `20defa9e0ece5da65fce49fad39659fe469293299d4693a2ef76bbb9ae1b2cf3` |
| Deterministic 38-member tar.xz | 1,169,468 | `c83b722a8049907ffb7d372c692bd2a1b1c4ba3e7b8d6d3db5c7f8dbd2a21c42` |
| Original handoff ZIP | 1,380,978 | `48d5422067e212ebc67aaf3febc9af65fa09a2b61cd1413ad246df5e9f4b22d0` |

The tar.xz is reported to exclude only `source/__pycache__/audit.cpython-313.pyc`. Twenty part entries `00.txt`–`19.txt` in `PUBLICATION.json` are absent as files. `PUBLICATION_HOLD.md` also mentions a deliberately unreferenced manually staged object; this archive neither retrieves nor adopts it. No local-only bundle, blocked recovery route, inferred file content, or replacement evidence has been used. The complete missing bundle cannot be reconstructed from these hashes and summaries.

## Retained local result, explicitly reported

The owner and original `RESULT.json` report one consumed local allocation: 3,025 two-evidence/two-claim rule structures × 9 conditions plus 12 directed cases, totaling **27,237 records**. The reported outcome is:

- `CLEAR_AND_REDERIVE` and `FULL_REBUILD`: zero false-retain and zero false-remove cases against a separately structured all-closed-model grounded oracle
- `LOCAL_SUPPORT`: 2,645 false-retain cases / 3,921 claims
- `BLIND_INVALIDATE`: 1,306 false-remove cases / 1,755 claims
- 15,135 deletion cases and 12,102 no-change cases
- Raw auditor: 700,837 checks, `errors=[]`; ten effective evidence corruptions rejected

Those results remain historical reports. This preservation did not restore the raw rows, re-audit them, rerun controls, establish source/process lineage for the complete local study, or reproduce the reported result. A same-author separate oracle is not independent human review. Absent publication is not a replacement scientific FAIL and does not create unused allocation capacity.

The stated model assumes finite positive OR-of-AND rules, complete and unchanged dependency declarations, fixed graph/rule structure, evidence deletion only and trustworthy evidence identity. Negation/default reasoning, probabilistic support, concurrent mutation, hidden dependencies, source authenticity/currentness, GUI/model/task effects, action authority, latency/tokens and production integration remain outside the demonstrated scope. Clear-and-rederive is presented as an application of established recursive-view/truth-maintenance practice, not a new algorithm.

## Continuing delivery boundary

At the 2026-10-01 preparation snapshot, main `7dbe196b8d1fb519139d15240ecb3f377a07b51d` lacked this package namespace. The original branch still pointed to the exact head above; #4443 was open Draft, #4431 was open, and the latest owner comment remained the publication HOLD update linked above. These bounded, non-atomic reads do not prove absence from every other branch, local workspace or unreachable object. Publication must refresh these guards before applying the prepared packet.


The original Draft, branch and owner Issue remain open and unchanged. Closed predecessors #1816 and #1850 remain unchanged; parent #1659 and the global ROADMAP remain open. This archive neither authorizes merging #4443 as complete evidence nor satisfies its outstanding raw-delivery gate.

- **H:** the already-consumed study's exact retained evidence can be made fully reachable and independently read back
- **T:** any later authorized delivery repair must use the existing #4431/#4443 track, preserve exact source/raw/audit/control/process bytes and establish lossless fixed-commit reconstruction and scoped read-only review
- **D:** `HOLD_REMOTE_RAW_DELIVERY` persists until complete byte delivery, exact readback, read-only reconstruction, applicable checks and scoped review satisfy that existing gate
- **C:** readable source, proof, aggregate result, hash commitments, CI success or this archival entry cannot substitute for the missing bundle
- **U:** raw validity, complete process lineage and independent reproducibility remain unestablished by this archive; no runtime, model/task benefit or performance promotion follows

No source, retained verifier, auditor, control, test or scientific matrix was executed. No new experiment was launched. Verification was limited to read-only GitHub retrieval and local byte/hash/tree/metadata checks. No shared index, remote object, branch, PR or Issue was edited during preparation.
