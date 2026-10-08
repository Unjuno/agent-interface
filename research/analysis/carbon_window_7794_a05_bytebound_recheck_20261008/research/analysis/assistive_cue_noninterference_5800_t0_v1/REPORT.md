# Issue #5800 — Assistive cue non-interference synthetic T0

## H/T/D/C/U

- **H:** A private model-only cue or genuinely passive shared cue can preserve this fixture's declared interaction signals; an intrusive cue is detected; an unavailable assistive-technology (AT) observation surface yields HOLD.
- **T:** Four finite cue conditions (none, private model-only, passive shared, intrusive shared negative control), plus unavailable-AT HOLD; exhaust all 512 combinations of nine binary invariant signals.
- **D:** Method-only scoped pass requires all three non-intrusive controls to pass, intrusive control to fail, unavailable oracle to HOLD, all 511 nonempty fault profiles to fail, clean profile to pass, and corrected raw-only audit to agree.
- **C:** Deterministic synthetic observations only. No GUI, screen reader, accessibility API, keyboard device, actual task, participant, or personal desktop was used. Docker was unavailable; see `ATTEMPTS.md`.
- **U:** No inference about lived accessibility, WCAG conformance, native overlays, browser/OS interoperability, cognitive load, contrast, or production non-interference. Only nine synthetic binary invariants and a synthetic task-effect surrogate are covered.

## Result

`METHOD_PASS_SCOPED` after transparent auditor repair. Candidate tests: 4 passed. Corrected raw-only audit: 512 profiles seen; 511/511 nonempty fault profiles detected; intrusive negative control failed; unavailable AT oracle returned HOLD. The original failed audit remains in `audit.raw.txt`; the corrected audit is a separate raw file. The candidate was executed only once.

This repairs a test-harness encoding mismatch, not a product defect or accessibility claim. Initial mask convention: candidate bit 1 means that axis was injected false; the first auditor interpreted bit 0 as false. The corrected auditor matches the candidate's documented encoding.

## Protocol and sources

Frozen inputs are recorded in `FREEZE.json`. W3C WCAG 2.2 and WAI-ARIA APG are used only as inspiration for web interaction invariants, not as native-desktop requirements or a conformance evaluation. The cited WCAG Understanding documents are informative guidance. See source URLs in `FREEZE.json`.

Reproduce from this directory with `python candidate.py`, `python audit.py`, and `pytest -q test_candidate.py`; auditor expects this directory as current working directory. The captured candidate raw was not regenerated for the corrected audit.
