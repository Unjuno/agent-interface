# Issue #6492 T0 — pre-registration

## H / T / D / C / U

- **H:** A source-bound preserved view and optional user-authored prospective cue can be represented in a return-to-work protocol without changing task identity, turning a cue into authority, hiding external state change, or delaying emergency release. T0 tests the protocol/auditor, not whether the view or cue improves human memory or task performance.
- **T:** Self-contained host-CPU method test derived from Issue #6492 T0. Six non-sensitive synthetic tasks × three arms (`timing_only`, `preserved_view`, `optional_cue`), with identical interruption question/answers/facts across arms. Candidate sees only the synthetic fixture. An independent auditor uses a separate oracle to verify source/task/window/surface/version binding, matched facts, changed-state warnings, cue offer/use/provenance, absence of automated effects, and immediate emergency release. Apply six mutations: swapped task/window, stale cue after external edit, forged agent-authored cue, duplicate save, missing offered-cue field, and delayed emergency release. No container was started because the shared WSLc interval was unassigned; the T0 is a deterministic CPU protocol validation and does not call repository runtime code.
- **D:** `METHOD_PASS_SCOPED` only if all 18 expected rows are present in exact order, arm facts match, source views are bound and historical when state changed, stale user cue is withheld, cue remains user-authored/optional, emergency delay is 0 ms, no automated task effect or oracle action leaks, and all six mutations are independently rejected. Any missing condition is `METHOD_FAIL`; no retry.
- **C:** Same synthetic interruption content and answer choices in all arms. Only view preservation and cue affordance vary. A view/cue is memory context, never authorization or proof of fresh state. Changed-state warning is identical across arms.
- **U:** One authored six-case synthetic fixture; no people, real/private app content, GUI, model, real effect, user memory, return-time measurement, usability/security/product result, or generalization claim. This does not authorize T1; consent/privacy/accessibility review remains separate.

## Frozen execution

- Repository main observed at issue/protocol intake: `b6c16aa4e505f6bc2c206bf9d078e3042be91ce9` (2026-10-02 03:35 UTC). The candidate/auditor below are self-contained host-CPU protocol code and do not load or modify repository runtime code; this is provenance context, not a current-main equality gate.
- Inputs: `fixture.json` and separate `oracle.json`. Formal output path: fresh temporary directory created by the one-shot run wrapper; candidate raw and audit JSON are retained in this evidence directory after successful validation.
- Candidate command: `python candidate.py --fixture fixture.json --output raw_candidate.json` — exactly one formal invocation.
- Auditor command: `python audit.py --fixture fixture.json --oracle oracle.json --raw raw_candidate.json --freeze FREEZE.json --output audit.json` — exactly one separate invocation, only if candidate exits 0.
- Construction tests are separate from formal invocation. No retry, no container, no GPU/CUDA, no human contact, no screenshots/private-app collection, no model, no actual user effect.
