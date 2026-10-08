# Issue #1936 successor — attention cue provenance integrity

## H/T/D/C/U

- **H:** Typed provenance makes attention cues explainable and prevents incomplete or authority-escalating cues from being treated as valid.
- **T:** Validate observed and inferred cues against required region, source, confidence, timestamp, frame, change, kind, and non-authority fields; reject missing provenance, invalid confidence, and authority escalation.
- **D:** `experiment.py`, five cases, validator verdicts, and SHA-256 result digest.
- **C:** Complete observed/inferred cues pass; missing frame, invalid confidence, and authority=true fail closed.
- **U:** Detector quality, model usability, GUI correctness, latency/token effects, and runtime integration remain unknown.
- **STOP:** One finite standard-library fixture; no model, GUI, network, runtime, or user input.

## Result

Command: `python experiment.py`

- Valid observed cue: accepted.
- Valid inferred cue: accepted as a cue, not authority.
- Missing frame, invalid confidence, and authority escalation: rejected.
- Result digest: `c995870b0579413c75730c7fc15427adb887e6477a49febc0d1115e241346609`.

**Decision: PASS_ATTENTION_PROVENANCE_INTEGRITY_SCOPED.**

This verifies only schema-level provenance integrity. It does not establish detector accuracy, model benefit, GUI correctness, latency/token savings, or runtime promotion.
