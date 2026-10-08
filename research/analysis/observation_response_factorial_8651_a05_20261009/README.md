# Issue #8651 A05 — corrected raw-only audit

## Purpose and lineage

A05 does not rerun the A04 candidate or alter A04's retained outcome. It audits the immutable A04 raw ledger (96 rows; SHA-256 `7c9ef1852727b1906681e6b8d1d36d2592c55c100589551710dcd381beaf600e`) with a corrected auditor. The original A04 audit file is retained as a comparison input.

A04's auditor ran row checks and all four corruption controls, but its self-tests mutated the shared protocol object's stored contrasts; the last forged-effect case overwrote the primary result from -1.0 to -0.875. A05 snapshots the raw-ledger contrasts before running tests and uses independent protocol copies for each mutation. This is an auditor-only successor: candidate invocations in A05 are zero.

## H / T / D / C / U

- **H:** For the retained A04 data, deadline/transient-cue difference-in-differences is at least 0.50 in magnitude, with each control interaction at most 0.10.
- **T:** Verify the upstream raw checksum and run the corrected independent auditor over all 96 immutable rows in pinned Docker, including all four mutation controls.
- **D:** PASS_METHOD_SCOPED requires checksum match, all row/timing/receipt checks, and rejection of all corruptions. INTERACTION_SUPPORTED_SCOPED additionally requires the frozen primary and control thresholds.
- **C:** The conclusion remains only a result of this deterministic constructed schedule; it does not demonstrate live system behavior.
- **U:** No inference about GUI/OS scheduling, models, safety, mediation, or user tempo.

## Provenance

Input commit: `5351d81439e0f8252d458b804c688b92a03b14ab`; source raw path: `research/analysis/observation_response_factorial_8651_a04_20261009/results/first-outcome/RAW.jsonl`; A04 audit path: `research/analysis/observation_response_factorial_8651_a04_20261009/results/first-outcome/AUDIT.json`. The result branch is based on the A04 evidence branch so an integration PR carries both the raw ledger and its corrected audit. A04 artifacts remain unchanged.
