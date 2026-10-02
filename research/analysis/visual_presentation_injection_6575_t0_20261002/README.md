# Issue #6575 presentation-transform T0

## H / T / D / C / U

- **H:** A deterministic observation packager can preserve source-pixel provenance and refuse crop-only views that hide independently annotated task or safety regions, across matched instruction, benign-text, and instruction-free-distractor fixtures.
- **T:** T0 only. A finite synthetic PPM deck is transformed into FULL, FULL+CONTEXT_CROP, CROP_ONLY, and SHAM_CROP packages. A separate raw-only auditor reconstructs crop bytes, verifies source hashes and arm completeness, and checks visibility/refusal against fixture annotations. No model, GUI, network, GPU, user data, credential, or effect is involved.
- **D:** `PASS_METHOD_SCOPED` only if every valid transform has exact byte provenance and the auditor accepts it, while each intentionally hidden task/safety-region crop is refused. Any mismatch is FAIL; missing/invalid inputs are HOLD/STOP. No susceptibility result is possible at T0.
- **C:** Synthetic colored regions and hand-authored rectangles may make mechanical checks easier than real screenshots. Pixel containment is not a semantic legibility or answerability oracle. A crop that retains annotated rectangles may still omit context needed by a human or model.
- **U:** Does not test prompt injection, model response, crop-induced proposal shifts, real GUI risk, or security of an integrated route. Only a separately authorized, preregistered T1 can estimate the interaction described in #6575.

## Freeze and allocation state

Planning main: `7c788b3df33928d84b327bb8b4b0ac8690de13c3` (2026-10-02).
This package is prepared on `research/visual-presentation-injection-6575-t0-20261002`.
The WSLc invocation is **not yet authorized or run**; this is source preparation only. Before a single candidate and independent auditor invocation, require an explicit bounded CPU/WSLc assignment on #5085, refresh main/branch/path/container collision checks, and regenerate the source/image freeze at launch. Reuse only the cached digest-pinned Python image; no pull/build. Network disabled, source read-only, outputs unique and separate, retries zero. Record cgroup warnings and make no resource-enforcement claim.
