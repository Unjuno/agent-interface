# Source lineage and rescue qualification

This package preserves the original first-run evidence from abandoned draft PR #8317 without rerunning or repairing the consumed allocation.

- Original branch: `research/proactive-interference-5947-t0-a01-20261007`
- Original head: `8ddb9557cde125604d05c2e0ad0c46a040400a10`
- Original base/freeze source: `798ac5ad709168ff1d27b115f10f4f96b126bb71`
- Original package-add commit: `a7262ca689e...` (`research: retain #8313 fixture audit coverage hold`)
- Original index commit: `8ddb9557cde...` (`research: index #8313 retained result`)
- Rescue uses an additive path on current main. `FORMAL_RUN.json`, `FREEZE.json`, raw bytes, manifest, candidate, auditor, report, and post-run review are carried byte-for-byte from the original branch. The rescue does not claim the old freeze is current-main evidence; the report remains explicitly bounded to the recorded old base.
- Original construction result (5/5) is historical. Rescue-local checks validate construction, indexes, and file integrity only; candidate/auditor were not invoked again.

The scientific disposition stays `HOLD_AUDITOR_COVERAGE`. The independent-auditor coverage gap documented in `POSTRUN_REVIEW.md` is unresolved; no model or proactive-interference conclusion follows.
