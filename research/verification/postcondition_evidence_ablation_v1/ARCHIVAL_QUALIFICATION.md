# PR #3960 archival qualification: provenance/STOP record only

This note qualifies preservation of three already-published, non-executable
historical files. It is not recovery of the experiment's missing source or raw
bundle, a fresh scientific audit, permission to execute anything, or satisfaction
of the owner's complete-delivery gate.

## Exact preserved material

- Source: [Draft PR #3960](https://github.com/Unjuno/agent-interface/pull/3960),
  owned branch `research/issue-3951-postcondition-evidence-ablation-v1`,
  head `bc98192c51a51b926c76a1533cc5568fbb48cc23`.
- Owner: [Issue #3951](https://github.com/Unjuno/agent-interface/issues/3951).
  It is open; the source PR is open/Draft in this preparation readback.
- Original namespace: `research/verification/postcondition_evidence_ablation_v1/`.
  Its entire published package is exactly three files, totaling 11,053 bytes:
  `AUDIT.json` blob `79ec1e1a4f1174a47dbb30715d5285058d3b0d1d`,
  `FREEZE.json` blob `ddb8b86cb1478348d761fb5007c91d3f99ae72be`,
  and `REPORT.md` blob `10e7909a44bb2e919790f3496b467fe92fb3e336`.
  All original paths, modes (`100644`) and Git blob identities are preserved.
- Original package tree: `41a978501678a5e4647e998c588fd1184b243f4b`.
  Each fetched file's bytes, size and Git blob hash were checked locally.
  Rebuilding the tree from the three path/mode/blob tuples matched this identity.
- Preparation base: main `f346b787a5a31381f51c0b7bd19740c3c7380db7`,
  root tree `e70f91a9b38f214b3ef833707f48b5280bfb4b7a`.
  The complete nonrecursive verification tree
  `56a9c406eecaf6ab65cff93cf024dd8127001dd9` establishes the original namespace
  is absent at this base.

This separate qualification and one navigation entry in the existing
`research/README.md` are new commentary. The historical reports and their
date/allocation labels are not rewritten. Relevant PR/code searches and the
existing `research/archive/` and `research/archives/` directory inventories
found no matching archive. This is a bounded discovery check, not a
repository-wide proof that no same-content copy exists.

## Useful knowledge and its evidence boundary

The retained report describes a transfer question: whether file-receipt
postcondition decisions depend on typed, complete evidence and an independently
authored expected contract rather than scenario labels or equality of missing
values. Its account of more explicit cleanup/contract information is a protocol
change, not an equal-information efficiency comparison.

The source reports one formal orchestration, 24 real child/file allocations and
72 paired consumer evaluations; candidate 3 PASS / 6 FAIL / 63 ESCALATE; 30 legacy
unsupported PASS decisions and one valid-save refusal under the new contract;
zero raw-audit errors; and 12 rejected corruption controls. It also reports seven
excluded construction methods and 97 later storage checks. These remain
historical reported outcomes. The receipt's `PASS_RAW_AUDIT` and
`PASS_EVIDENCE_BOUND_POSTCONDITION_SCOPED` are not a new audit or a promotion
conferred by this archive. Missing source/raw prevent independent verification
of those results from this three-file record.

The original label-bound #3048 result is not retroactively invalidated.
[Issue #3217](https://github.com/Unjuno/agent-interface/issues/3217) retains
ownership of predecessor source/artifact reconciliation. No predecessor
allocation or outcome is modified, pooled or rerun.

## What remains missing

The frozen manifest names nine source/plan/schedule files. A read-only lookup of
each exact declared Git blob resolved only `legacy.py`:
`0cd6b755cf54d8c01b254b2f8ee52610a29410f2`, 3,083 bytes. That same blob is
already on preparation main at
[`known_postcondition_boundary_v1/experiment.py`](../known_postcondition_boundary_v1/experiment.py).
It is not newly recovered #3951 implementation and is not duplicated here.

The other eight declared Git blobs returned 404 through the repository API:
`PLAN.md`, `audit.py`, `candidate.py`, `controls.py`, `producer.py`,
`run.py`, `schedule.json`, and `test_construction.py`. These results establish
unavailability through these exact read requests, not permanent loss or absence
from every machine. No bytes were reconstructed from the hashes or narrative.

The retained [delivery checkpoint](https://github.com/Unjuno/agent-interface/issues/3951#issuecomment-5766323551)
distinguishes two missing inputs:

1. The exact frozen source/plan/schedule package, bound by `FREEZE.json`.
2. The conversation-only, non-executable data ZIP, declared SHA-256
   `95c96bcd83a7812d25712a67dc6ff64ecadc6f2d3902cd463bc92dde50357d0f`.
   It reports 116 ZIP entries including 110 execution/construction evidence
   files and supporting records. **That ZIP explicitly excludes executable
   sources**, so recovering it alone would not complete source delivery.

The declared raw file is
`formal/postcondition-evidence-ablation-20260922-01/raw.json`, 75,609 bytes,
SHA-256 `ef18a94170dc7cc84170b56ff7c20eb2f75f2616cda1c6c7d66fc4721f77118e`.
Neither ZIP nor raw was recovered or rehashed for this archive. Later Issue/PR
comments record unsuccessful bounded filename/digest searches; they are not
proof of absence elsewhere. Their historical recovery claims are separate
from the exact Git-object lookups performed for this preparation.

The [cross-archive recovery comment](https://github.com/Unjuno/agent-interface/issues/3951#issuecomment-5866318302)
is headed `2026-09-29`, while GitHub records both its `created_at` and
`updated_at` as `2026-09-28T08:29:18Z`. This date discrepancy is retained
explicitly; neither the historical heading nor the API timestamps are
normalized, and no corrected event date is inferred.

## STOP, ownership and next work

The controlling disposition remains
`STOP_SOURCE_PUBLICATION_TOOL_SAFETY_CHECK` / HOLD.
This archive only reuses the three successfully published non-executable blobs;
it does not retry the blocked executable-source publication through another
route. It does not mark the source PR ready, close #3951/#3048/#3217, authorize
branch deletion, or satisfy complete scientific delivery/main integration.
Retain the original branch while the live PR/evidence dependency remains.

The concrete next step is to obtain retrievable original source bytes and the
separate original data package under #3951, verify their exact declared
identities, and retain a readback trail. Do not treat a report, manifest, legacy
file or data-only ZIP as the complete source capsule. Do not reconstruct missing
records, substitute new output, or repeat consumed allocation
`postcondition-evidence-ablation-20260922-01` (historically one invocation,
zero retries).

No experiment source, tests, audit scripts, model, container, GUI or formal
allocation was executed for this preservation. Complete exact-byte
source/evidence delivery and independent repository-based verification remain
open. Any later live producer-binding/entry-path test requires a separate
reviewed allocation; this archive grants none. The original supplied
Linux/CPython file/JSON scope has no Docker image identity and establishes no
model/task usefulness, production runtime, cross-platform, latency/token,
authentication, crash-durability or causal-effect claim.
