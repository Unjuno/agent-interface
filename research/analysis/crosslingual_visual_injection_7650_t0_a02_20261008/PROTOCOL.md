# Issue #7650 T0 A02 — read-only row-binding audit successor

## Purpose and immutable predecessor

This successor repairs only the audit-coverage gap identified by independent review of A01. It does not rerun or alter A01 candidate/auditor artifacts. Input is the exact immutable A01 `RAW.json`, SHA-256 `c11da4fd1f062127a13e253e35536440d0a9b08c45ef48a639843a5f7597ccc7`.

## H / T / D / C / U

- **H:** A raw-hash-bound independent read-only auditor that parses each UID and compares its family, task language, embedded language, class, and variant to the same row's fields will reject both single-row and coordinated aggregate-preserving metadata corruption while accepting the frozen raw input.
- **T:** Test the auditor on the A01 raw bytes, then preregister and invoke the frozen A02 auditor once. Its own controls mutate one row's task language, swap task-language metadata between two rows while preserving marginal counts, mismatch class/source/UID fields, hide/outbound the target metadata, and alter the adjudication status. It also rejects any raw-byte hash mismatch.
- **D:** A01 raw bytes and SHA above; A02 auditor/test/freeze hashes; one audit output and exit code. No candidate run and no new corpus rows.
- **C:** `PASS_ROW_BINDING_AUDIT_SCOPED` only if the frozen predecessor raw passes, all expected IDs map exactly to same-row fields, 960 unique IDs and 12 balanced cells are reconstructed, and every seeded corruption is rejected.
- **U:** This is bookkeeping validation only. There are no linguistic stimuli or screenshots. English/Turkish semantic equivalence, naturalness, pixel visibility/legibility, model susceptibility, and any security effect remain unknown. Issue #7650 full T0 stays HOLD.

## Execution

Host-only Python stdlib. Do not invoke A01 again. After preregistration, run A02 auditor exactly once:

```sh
python3 research/analysis/crosslingual_visual_injection_7650_t0_a02_20261008/audit.py \
  research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/RAW.json
```

Construction tests are not the formal audit. Preserve the first formal outcome; no retry.
