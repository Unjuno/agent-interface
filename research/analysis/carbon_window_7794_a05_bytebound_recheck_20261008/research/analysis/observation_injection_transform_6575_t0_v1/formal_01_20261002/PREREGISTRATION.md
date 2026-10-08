# Preregistration — Issue #6575 T0

## H / T / D / C / U

- **H:** A source-preserving deterministic presentation fixture can maintain exact source-pixel lineage and legitimate target/safety visibility for the declared context-crop arms, while rejecting a crop that hides either required region. This is a method feasibility hypothesis only; it does not test model susceptibility.
- **T:** Six synthetic scenes = 3 stipulated content classes (`BENIGN`, `UNTRUSTED_INSTRUCTION`, `DISTRACTOR`) × 2 user-panel layouts (`LEFT`, `RIGHT`). Each scene is transformed to four arms (`FULL`, `FULL_PLUS_CONTEXT_CROP`, `CROP_ONLY`, `FULL_PLUS_SHAM_CROP`) for 24 case/arm rows. A separate candidate gate emits two intentionally invalid crop decisions per scene (12 checks total). A raw-only independent auditor reconstructs all image pixels, hashes, source boxes, arm membership, target/safety visibility and invalid-crop decisions from the oracle. No image contains readable attack text; category labels are stipulations, not observed semantics.
- **D:** `PASS_METHOD_SCOPED` only if all 24 rows are present exactly once, all 36 output-image items exactly reconstruct from the deterministic source and transform, all six valid context crops retain the whole target and required safety boxes, same-size sham/context geometry agrees, and all 12 invalid crop checks return REJECT for the correct omitted region. Any byte/box/hash mismatch, hidden target/safety, invalid crop allowed, missing/duplicate row, or missing invalid check is FAIL.
- **C:** A passing raster-construction check says nothing about legibility, model interpretation, image-token preprocessing, task answerability beyond stipulated pixel regions, or proposal changes. Magnification and crop geometry remain potential confounds for a later model rung.
- **U:** The content-class labels and target/safety meaning are synthetic oracle stipulations. No attacker text is rendered as readable language; no model, provider preprocessing, live UI, proposal, human, authorization sink, or effect is sampled. No vulnerability or safety conclusion follows.

## Protocol

Allocation: `OBS-INJECTION-TRANSFORM-6575-T0-20261002-01`. One native WSLc construction, one candidate transform, one independent audit; zero retries. Pinned cached Python image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; no pull, network disabled, CPU 1, requested memory 1 GiB, UID 65534. No GPU, Docker, Podman, GUI, model or external effect. Retain WSLc resource warnings verbatim; configured memory is not assumed enforced.

Candidate has read-only access only to staged `candidate.py` + `scenes.py`; it cannot read `auditor.py` or `oracle.json`. Auditor has read-only access only to staged `auditor.py` + `oracle.json` and byte-identical candidate raw input; it cannot read candidate source. Outputs are isolated and initially empty under `construction/`, `candidate_output/`, `audit_input/`, `audit_output/`.

Formal invocation counts at this preregistration commit: construction=0, candidate=0, auditor=0. `FREEZE.json` records the base main SHA and SHA-256 hashes for all source files/staged copies; no source edit is permitted after freeze. Failed formal rungs are retained and not retried.
