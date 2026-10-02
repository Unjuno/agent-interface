# Preregistration — Issue #6519 T0

## Question and hypothesis

Does an optional, source-bound semantic-affordance card remain a non-authoritative hint across a finite set of correct, missing, stale, unsupported, and contradictory observations, while preserving independent raw evidence and UNKNOWN? The Issue's broad H concerns model/task benefit; this T0 can only validate the integrity/exposure method needed before a model study.

**T0 H:** the canonical annotation ladder will expose only current, observation-bound claims at each declared precision level; never infer goal appropriateness, action authority, or task completion; and never hide raw evidence or erase UNKNOWN. Five planted faulty implementations will each be rejected by an independent raw-only auditor.

## H / T / D / C / U

- **H:** As above. No directional claim about model choices or user benefit.
- **T:** Eight deterministic GUI-like observation/card rows, four canonical arms (`RAW_ONLY`, `MODE_LABEL`, `CANDIDATE_EFFECT`, `UNCERTAINTY_CONTRADICTION`) and five deliberate corruption arms (`DROP_SOURCE_BINDING`, `FLIP_EFFECT_LABEL`, `SUPPRESS_UNKNOWN`, `CARD_AS_AUTHORITY`, `HIDE_RAW_EVIDENCE`). A candidate serializes all 72 case/arm rows from `fixture.json`, which contains no effect-truth oracle. A separate `oracle.json` is mounted only for an independently implemented raw-only auditor to recompute source, surface, generation, mode, effect-label, uncertainty, authority, raw-fallback, and completion invariants. Incorrect source-matched effect claims may be emitted only as `UNVERIFIED` and are recorded as oracle disagreements, never as application effect. Construction tests include deliberate output corruptions.
- **D:** `METHOD_PASS_SCOPED` only when all 32 canonical rows independently satisfy the frozen contract, every incorrect exposed effect claim remains explicitly unverified, each of the five corruption classes is independently detected on its designated witness, all eight cases and arm denominators are present exactly once, and no auditor errors remain in canonical rows. Any canonical unsafe authority/completion or missing raw fallback is `FAIL_METHOD`. Hash, parse, count, or audit execution failure is `STOP`. A passing result is a finite contract-method result only.
- **C:** The fixture truth and effect labels are stipulated synthetic values. The test does not establish that any real affordance is true, that a model notices metadata, or that extra annotations help a task. A separate model/GUI study is required.
- **U:** No stochastic model, live UI, task effect, application, OS, external side effect, human, token, latency, or production runtime behavior is sampled.

## Frozen cases

1. Current genuine modal with matching evidence.
2. Current normal sheet with a matching non-modal annotation.
3. Modal absent while an old modal card remains.
4. Lookalike dialog whose effect differs from the card.
5. Focus moved to another surface.
6. Target generation changed.
7. Unsupported mode label.
8. Source-matched card implies save completion while the auditor-only effect oracle remains pending; the candidate must not receive that oracle and any surfaced effect statement stays `UNVERIFIED`.

## Controls and invariants

- Every exposed claim binds to exact observation, surface, and generation.
- Operational availability, possible effect semantics, goal appropriateness, authority, and application completion are separate fields.
- Unsupported, stale, missing, and contradictory evidence yields UNKNOWN and does not promote the card.
- Raw image/evidence remains available in every arm.
- An affordance card never grants authority and never proves task completion.
- Mutant arms are negative controls only; the auditor must flag their raw violations rather than trust a candidate-supplied mutant label.

## Reproducibility and allocation

Main base at freeze, complete file hashes, pinned image/runtime, exact commands, output paths, one-shot limits, and UTC timestamps are in `FREEZE.json`. Fresh #6519 issue/comment/branch/PR searches found no owner allocation. #21 is the adjacent semantic-affordance proposal; this allocation tests only #6519's optional-annotation regression envelope and does not implement #21. No model or GUI allocation is requested.

Formal budget: construction=1, candidate=1, independent auditor=1, retries=0. The candidate and auditor output directories must be fresh before each invocation. Do not rerun a consumed formal rung or edit frozen sources.
