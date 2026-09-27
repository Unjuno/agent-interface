# Issue #4603 — immutable #4293 evidence reconciliation

## H / T / D / C / U

**H.** The 60-case #4284 allocation recorded by PR #4293 can be independently reconciled from its immutable Git evidence without rerunning either historical allocation, while preserving the separate merged 24-row PR #4292.

**T.** Read-only GitHub MCP intake found PR #4292 merged with 24 lifecycle rows/raw SHA-256 `dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31`; PR #4293 remains open/non-mergeable, with 60 formal cases / 462 nested rows/raw SHA-256 `711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9`. Both records were preserved as distinct.

The PR #4293 tip `393c4115add5e602ed279388a93dad4094daa687` contains only the generated index refresh; it points to an earlier frozen evidence branch state. Authenticated read-only Git fetch and `git cat-file blob` extracted the exact frozen evidence files without checking out/modifying a worktree. All four compressed evidence-part blobs matched their declared byte counts and SHA-256 values. The frozen `unpack_evidence.py` was run once in local Docker `python:3.12-slim-bookworm`, image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64, with `--pull=never --network none --read-only --memory=512m --cpus=1 --pids-limit=32`, read-only source mount and separate empty output. It verified concatenated XZ bytes and source/raw hashes before safely extracting 19 files.

Verified raw:
- `formal-01/RAW.json`: 217,321 bytes; SHA-256 `711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9`.
- 60 cases; 10 schedules × 3 policies × 2 repetitions. Each of the three policies has 20 cases; each of ten schedules has six cases.
- Nested lifecycle `rows`: 462.
- No row authority grants.

Independent local Docker verification (same pinned image/constraints):
- Frozen raw-only `audit.py` recomputation: decision `PASS_VERSIONED_PREDICATE_SPECIALIST_SWITCH_SCOPED`, case_count 60, stable ratios [0.25, 0.25], errors=[].
- Frozen copied-evidence corruption test: pass=true, 13/13 declared mutations rejected.
- Formal runner was not invoked; no case/row was generated.

The initial GitHub Contents route returned 404; authenticated Git object fetch was the successful retrieval path. Two wrapper-only Docker attempts are retained in the task transcript: an existing-output refusal, then an audit output mistakenly mounted read-only. Both stopped before changing source/raw or running a formal study. The successful run used a distinct empty output and separate writable audit directory; raw inputs remained read-only.

**D.** `PASS_EVIDENCE_RECONCILED_60_CASE_DELIVERY` for immutable artifact integrity and the frozen raw-only audit. This does not retroactively merge PR #4293, rewrite Issue #4284's closure scope, select between the distinct 24-row and 60-case historical outcomes, or establish Issue #4295's regeneration comparison.

**C.** Existing authored deterministic evidence only; no model/provider/GUI/OS input/networked container, no credential inspection, no runtime modification, no formal rerun. PR #4292, PR #4293 and predecessor files were not edited.

**U.** Which distinct historical result controls #4284 closure remains a repository governance/integration decision. The separate regeneration-vs-versioned-lifecycle hypothesis remains untested. No learned-model quality, natural drift economics, latency, energy, token, task/product or production claim follows.

## Provenance

- Successor Issue: #4603; related #4284/#4295.
- PR #4293 frozen source branch: `research/versioned-predicate-specialist-switch-4284-20260923`.
- PR #4293 reviewed tip: `393c4115add5e602ed279388a93dad4094daa687`.
- New evidence-only branch: `research/issue4603-evidence-availability-20260927`.
- Additive delivery path: `research/integration/issue_4603_evidence_availability_20260927/`.
- Docker image: `python:3.12-slim-bookworm`, `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`.
- No edits to #4292/#4293 artifacts, generated indices, runtime, or roadmap.
