# Archival qualification: allocation-03 local preflight

Prepared 2026-10-02 from original PR #5649 head
`121d89a94590cf9922e2c0c9d7083b01e7105e13`.
This is archival preservation of the historical preflight package, not a recovered formal result or authorization to execute.

## Disposition and missing evidence

The frozen record has `formal_authorized=false`, `formal_invocations=0`; the retained unit summary reports scientific sessions and physical inputs zero. The planned eight formal sessions were not an observed denominator. No attack-onset H/T/D/C/U decision was made: PLAN.md describes an experimental design, not observations.

`UNIT_TEST_RESULT.json` reports 10/10 scoped construction/unit tests and binds `results/UNIT_TESTS.log` to SHA-256 `e782b4c7b7e5681cd85a574732185faf1b153408eb4759c9b9c174d078a9b68b`, but that raw log is absent from the 38-file package. The historical pass claim is retained as author-reported and is not independently recoverable from this package. No test was rerun or replacement log manufactured in this review.

README's eventual `RESULT.md`, `AUDIT.json` and `results/formal/` are absent. With formal invocations zero, those links are prospective and do not establish missing completed formal results. The approximately 80 MB offline runtime artifact ZIP is intentionally uncommitted; its manifest and hash are references only. The previously reported missing exact Docker image was not rechecked here and cannot be inferred from present repository access.

The historical `formal_gate` text is not a present execution authorization. In particular, merging/readback of this archive does not satisfy a new allocation's resource, source, image or user-authorization gates. No source, formal runner, unit suite, auditor, game, container, GPU or resource inventory was executed by this review.

## Fresh immutable-byte verification

- All 38 original paths: 4,072,437 bytes total. Their retrieved bytes reconstruct the published Git blob IDs.
- The 6,720-byte source capsule matches frozen SHA-256 `317068daacc2abafacc44b85e18c0b1ad468fa8eb185361fd9cdf3b247475e9e`; its six regular source members match the six source/ files exactly.
- The 3,316,472-byte runtime source archive matches Git blob `214bfc076e1f28c54165c2204f5613c92151824f` and frozen SHA-256 `94f16166c9588b97566bb5a4b32fb8d3a8358a835a9f5a15ac7ff88012703a0e`. All 2,592 regular members have safe relative paths and match the manifest's byte counts and SHA-256 values, with exact membership.
- All 11 embedded v12 dependency-manifest hashes and all 3 comparator-support blob/hash/size bindings match.
- Frozen Dockerfile, import preflight, input-verification record, v12 input-owner and adapter hashes match.
- All 10 JSON files parse and all 19 Python files parse as AST. Parsing/hashing does not execute archived source or verify historical behavior.
- The source archive/manifest and copied dependencies are frozen inputs, not updates to shared runtime dependencies. They remain isolated under this additive package root. They have not been upgraded to current-main versions.
- At main `f4fcea6a67f1d8695626447d97ae697fa454a04e`, this root was absent and comparison contained only 38 added package files. No runtime default, workflow, shared source or index changed.
- Original-head hosted replay-gate succeeded and formal was skipped. These are repository CI facts, not reproduction of the reported 10/10 unit suite or a scientific outcome.

## Owner and successor boundaries

The [rescue notice](https://github.com/Unjuno/agent-interface/issues/4223#issuecomment-5920815460), [dormant-branch review](https://github.com/Unjuno/agent-interface/issues/4223#issuecomment-5940942518), and [recovery-package audit](https://github.com/Unjuno/agent-interface/pull/5649#issuecomment-5941610735) identify the archive-only scope and unresolved raw-log/environment limits. This qualification does not assert a current resource lease or release on another owner's behalf.

Allocation 02, all startup-gate successors, and #4193's prior six-session result remain distinct. Preservation does not pool their evidence, retry this allocation, or close the still-open scientific Issue #4223. The historical 10/10 report remains qualified by the missing raw log; formal science remains NOT_EVALUATED.
