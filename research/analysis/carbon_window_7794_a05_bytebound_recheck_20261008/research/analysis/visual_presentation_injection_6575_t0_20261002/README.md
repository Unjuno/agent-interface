# Issue #6575 presentation-transform T0

## H / T / D / C / U

- **H:** A deterministic observation packager can preserve source-pixel provenance and refuse crop-only views that hide independently annotated task or safety regions, across matched instruction, benign-text, and instruction-free-distractor fixtures.
- **T:** T0 only. A finite synthetic PPM deck is transformed into FULL, FULL+CONTEXT_CROP, CROP_ONLY, and SHAM_CROP packages. A separate raw-only auditor reconstructs crop bytes, verifies source hashes and arm completeness, and checks visibility/refusal against fixture annotations. No model, GUI, network, GPU, user data, credential, or effect is involved.
- **D:** `PASS_METHOD_SCOPED` only if every valid transform has exact byte provenance and the auditor accepts it, while each intentionally hidden task/safety-region crop is refused. Any mismatch is FAIL; missing/invalid inputs are HOLD/STOP. No susceptibility result is possible at T0.
- **C:** Synthetic colored regions and hand-authored rectangles may make mechanical checks easier than real screenshots. Pixel containment is not a semantic legibility or answerability oracle. A crop that retains annotated rectangles may still omit context needed by a human or model.
- **U:** Does not test prompt injection, model response, crop-induced proposal shifts, real GUI risk, or security of an integrated route. Only a separately authorized, preregistered T1 can estimate the interaction described in #6575.

## Freeze and allocation state

Initial preparation main: `7c788b3df33928d84b327bb8b4b0ac8690de13c3` (2026-10-02); branch is synced to main `f891ccb0fabac44f43a0d05edfce5fac050e66f0`.
This package is prepared on `research/visual-presentation-injection-6575-t0-20261002`.
This is source preparation only. The scientific owner has since completed the same #6575 T0 question under allocation `OBS-INJECTION-TRANSFORM-6575-T0-20261002-01`; main retains its `STOP_HARNESS_FIXTURE_MISMATCH` under PR #6582. This duplicate package was never assigned or run (candidate/auditor 0/0), and must not be invoked or used to retry/repair that consumed allocation. See `PREPARATION_REPORT.md` and the follow-up on #6575.
