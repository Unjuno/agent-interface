# Issue #7650 cross-lingual visual-injection T0 A01 — machine-gate spike

## Disposition and H / T / D / C / U

This is a non-effectful, host-Python construction spike, not the complete Issue T0. The exact main base is `fabdb1de8273e8a87dfb2bea53856079da997998`. Issue #7650 is open; current branch and open-PR searches for `7650` returned no matches before work began. OrbStack Docker 29.4.0 is present, but inspecting `python:3.12-slim` failed with content-store `operation not supported`; no repair, pull, retry, or other container was attempted. Issue T0 does not require Docker. This spike uses Python stdlib only and has no model, network, GUI, participants, or external effects.

- **H:** A mechanically specified 2×2 task-language × embedded-instruction-language corpus can preserve cell, source-role, and synthetic target-geometry invariants and detect seeded provenance/visibility corruption. This does not hypothesize model susceptibility.
- **T:** Generate 40 English semantic-frame IDs, each crossed with English/Turkish task labels and embedded-content labels and malicious/benign/distractor classes. Keep generated translations explicitly unadjudicated. Audit all rows for unique IDs, 2×2 coverage, task/source labels, target visibility/geometry and deterministically corrupted provenance/visibility rejection. Independently reconstruct from raw bytes with a separate auditor.
- **D:** Frozen `candidate.py`, `audit.py`, `test_contract.py`; `FREEZE.json`; one candidate run and one independent audit run with captured raw bytes, exit codes and SHA-256. No translations are represented as validated; the tested language strings are metadata placeholders, not linguistic stimuli.
- **C:** `PASS_MACHINE_GATE_SCOPED` only if the candidate emits 40×2×3×4 = 960 unique rows, the auditor reconstructs all expected cells and source/geometry constraints, and both planted corruption classes are rejected. Any discrepancy is HOLD/FAIL. This cannot satisfy Issue #7650 `PASS_METHOD_SCOPED` because the required independent bilingual semantic/legibility adjudication and rendered screenshot/pixel review are absent.
- **U:** Translation equivalence, naturalness, attack-intent preservation, actual font/OCR legibility, model behavior, language-congruence effects, sample-size power, and real UI transfer remain unknown. No model or action proposal is evaluated.

## Preregistered command and invocation boundary

After freezing source bytes and the independent oracle, run each formal artifact once:

```sh
python3 research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/candidate.py
python3 research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/audit.py \
  research/analysis/crosslingual_visual_injection_7650_t0_a01_20261008/RAW.json
```

Construction tests are separate and do not count as formal invocations. No retry is permitted for either formal command; preserve any first failure as-is. The host-only environment is an explicit deviation from the preferred container workflow after the current OrbStack content-store failure. No Docker image identity is claimed.

## Issue T0 completion gate

Do not promote this spike to full T0. A later separately frozen successor must obtain an independent competent English–Turkish adjudicator, actual rendered screenshots, source/target annotation, and pixel/geometry legibility review. It must preserve disputed pairs as `UNKNOWN`, reject planted semantic inversions and label swaps, then independently audit the completed corpus before Issue-level `PASS_METHOD_SCOPED` can be considered. T1 remains separately frozen and gated.
