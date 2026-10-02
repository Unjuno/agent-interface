# Result — #6241 calibrated success-history transfer T0

**Disposition: `PASS_METHOD_SCOPED`.** The candidate and independent raw-only auditor each ran once (exit 0); retries=0. The construction suite passed 8/8 before the formal candidate. The auditor exactly reconstructed all eight rows and rejected all six frozen mutations.

## Observed discriminator

With the same 8-success/2-failure history, a declared same-latent-regime and unchanged-precondition link transferred the synthetic posterior mean (0.75) and crossed the frozen 0.70 proposal threshold. The identical streak in an independent regime remained at the base 0.50 and did not transfer. A changed route precondition or capability also reset transfer to 0.50. A same-regime 2/8 record transferred as evidence but remained below threshold at 0.25. An ambiguous effect forced HOLD and preserved `obligation-A-effect-77`; unknown dependency forced HOLD; private A history was not exposed.

This is an authored finite method fixture. It demonstrates that the frozen typed discriminator behaves as specified; it does **not** show that a real model makes this distinction or that prior task history harms or improves GUI decisions.

## Reproduction and provenance

- Frozen source main: `d7e8a932da27e7f271920de409b079fedc75dee1`.
- Before publication, the result branch was fast-forwarded from the frozen run base to current `main` `4da4257ad481e9a4ea79133bdaf93c962e686fe7`; intervening commits touched only unrelated #6383 evidence and `docs/IDEAS_AND_OUTCOMES.md`.
- Candidate: `python candidate.py --input fixtures.json --output candidate_output.json`; one invocation, exit 0, eight rows, output SHA-256 `7596030f166b37292dc2357cd0b2917f59938fd6d8cf929eb673e2b2e34af3f4`.
- Independent raw-only audit: `python audit.py --input fixtures.json --candidate-output candidate_output.json --output audit_report.json`; one invocation, exit 0, exact 8/8 reconstruction, 10/10 audit checks and 6/6 mutation controls; report SHA-256 `59ea4b37e5be2cfab6b925e77f786f223f2fef8f2dfab598281b9c90baf2880a`.
- Construction: `python -m unittest -v test_construction.py`; 8/8 passed before formal execution.
- CPython 3.11.9, Windows 10.0.26200, host CPU. No model, GPU/CUDA, GUI, WSL/WSLc, Docker, network, or external effects. This standalone T0 avoided the shared WSLc runtime while other tasks were coordinating it.
- Frozen inputs/source and full raw candidate/audit outputs are retained beside this report. SHA-256 manifest: `SHA256SUMS.txt`.

## H / T / D / C / U interpretation

- **H:** Untested for model behavior. This T0 only validates the deterministic transfer discriminator.
- **T:** Eight synthetic cases, fixed Beta(1,1) prior and 0.70 threshold; all outputs bound to allocation and frozen-main identifiers.
- **D:** Method-scoped PASS under the exact finite oracle and six corruption controls.
- **C:** Relation labels and synthetic counts are authored and treated as correct; no stochastic model, prompt, token position, or actual task is present.
- **U:** No empirical GUI proposal quality, human confidence, privacy/security guarantee, latency, effect correctness, broad generalization, or product claim.

The separate model-facing T1 in Issue #6241 remains untested and requires its own frozen contexts, fixed model and independent semantic oracle. This result neither authorizes nor consumes any GPU allocation and does not change the #5139 HOLD.
