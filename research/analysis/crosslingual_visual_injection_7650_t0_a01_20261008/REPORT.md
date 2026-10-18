# Issue #7650 T0 A01 machine-gate spike

## Result

`PASS_MACHINE_GATE_SCOPED` for a narrow authored bookkeeping fixture; **Issue #7650 T0 remains HOLD / incomplete**. The candidate generated 960 unique synthetic rows (40 family IDs × 2 task-language metadata × 2 embedded-language metadata × 3 content-class metadata × 2 variants). The independent raw-only auditor reconstructed the 12 declared language/class cells, found no baseline ledger errors, and rejected both seeded controls: an embedded-source label swap and a hidden/out-of-panel target mutation. All rows were explicitly marked `UNKNOWN_NOT_ADJUDICATED`; all stimulus fields were placeholders, not linguistic content.

This result does not meet the Issue's 40 bilingual semantic attack families. No English or Turkish sentence was authored or reviewed, no screenshot was rendered, and no pixel/geometry oracle inspected an image. The geometry mutation check verifies only that a record equals a fixed expected metadata object. It is not visual visibility or legibility evidence. No independent bilingual adjudicator was available, so meaning, naturalness, intent preservation, and translation equivalence remain unknown. There was no model, inference, tool proposal, GUI, participant, network, or effect.

## H / T / D / C / U

- **H (machine-only):** A fixed 2×2 language-metadata ledger can preserve cell and provenance invariants and detect planted ledger-level provenance/geometry-record mutations. No susceptibility hypothesis was tested.
- **T:** Frozen stdlib candidate generated 960 rows; one separate raw-only auditor reconstructed them and tested two mutations. Candidate and auditor each invoked once, with no retries.
- **D:** Base main `fabdb1de8273e8a87dfb2bea53856079da997998`; frozen script/protocol hashes in `FREEZE.json`; exact commands, counts, exit codes and raw/stdout hashes in `INVOCATIONS.md`.
- **C:** Machine fixture criterion passed: 960 expected IDs, balanced 12 cells, explicit UNKNOWN labels, and 2/2 seeded metadata mutations rejected. Full Issue T0 criterion not met: independent bilingual semantic and actual pixel/legibility adjudication are absent.
- **U:** Translation quality/equivalence; rendered visibility/legibility; model perception, reasoning or trust-boundary behavior; congruence effect; power/materiality; external validity.

## Execution environment and preserved setup failure

Host-only Python 3.14.5 on macOS 27.0.1 arm64, standard library. OrbStack Docker reported server 29.4.0, but read-only inspection of `python:3.12-slim` failed with a containerd content-store `operation not supported` error. No image was pulled, Docker state repaired, or command retried. This deterministic no-effect ledger spike did not require Engine API/isolation, so the eligible host CPU path was used and is not represented as a container run. No image digest exists.

Construction tests passed 4/4 before freeze. `py_compile` and `git diff --check` passed. A manifest helper had a syntax error before formal audit; it was corrected without changing frozen candidate/auditor bytes or the already captured raw result. The exact first formal outputs remain retained.

## Next evidence gate

Do not claim `PASS_METHOD_SCOPED` for Issue #7650 from this result. The minimum meaningful next step requires a competent independent English–Turkish adjudicator and a separately frozen successor that contains actual semantically aligned pairs, matched benign/distractor stimuli, rendered screenshots, and pixel-level visibility/legibility review. Ambiguous pairs must stay UNKNOWN; planted semantic inversions and provenance errors must fail closed. Only after those gates and an independent audit can the full T0 disposition be considered. T1 remains a separate model/resource/owner allocation; this work grants none.
