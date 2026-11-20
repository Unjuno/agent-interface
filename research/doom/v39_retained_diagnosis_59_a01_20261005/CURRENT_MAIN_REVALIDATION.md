# Current-main revalidation and preservation note

This additive rescue carries the retained #7875 diagnosis and the corrected v2 crosswalk from #7936 onto current main. The original `README.md`, `RESULT.json`, `FREEZE.json`, and their historical `SHA256SUMS` entries are preserved byte-for-byte. The v2 documentation is kept separately as `README_V2.md`; its independent manifest is `SHA256SUMS_V2`.

## Local gates

- Original frozen package manifest: 5/5 hashes verified.
- V2 manifest: 8/8 hashes verified.
- `test_diagnosis_v2` and `test_audit_v2`: 4/4 passed normally and 4/4 passed under Python optimized mode (`-O`).
- Python compilation of the historical and v2 producers, auditors, and focused tests passed.

## Scope and limits

These are deterministic retained-evidence reconstruction and integrity checks, not a game/model/controller/GUI/input replay, a formal candidate/auditor run, or evidence of live efficacy. The PR remains a draft pending independent review; no one-shot experiment was repeated. The source PRs and their frozen evidence remain unchanged.
