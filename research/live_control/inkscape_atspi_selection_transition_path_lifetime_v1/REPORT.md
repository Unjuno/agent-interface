# Inkscape AT-SPI selection-transition vs object-path lifetime

Task `INKSCAPE-ATSPI-SELECTION-TRANSITION-PATH-LIFETIME-20260917-031`, Issue #587.

**Decision: `REJECT_SELECTION_TRANSITION_ALONE_AS_DEFUNCT_CAUSE_SCOPED`.**

## Question

Earlier #415 construction observed labelled target paths becoming defunct in the complete standard AT-SPI selection-event setup. Prior one-factor work rejected Registry presence, listener registration, launcher-generated accessibility-bus lifecycle, app-side session discovery, and a session-discovery × listener interaction as sufficient causes under close/reopen fixtures. This rung asks whether **actually producing the `none -> A -> B -> none` document selection transitions** is sufficient while the full standard stack is held fixed.

## Frozen comparison

Both arms use official launcher/session `org.a11y.Bus` discovery, genuine Registry, exactly two registered listeners (`object:state-changed`, `object:selection-changed`), unmodified Inkscape 1.4 and the same labelled A/B SVG. Paths are dynamically discovered once before the phase sequence.

- control: empty-canvas click, empty-canvas click, Escape -> visual states none/none/none;
- candidate: click A, click B, Escape -> independently verified visual states A/B/none.

After every phase the **original** A/B object paths are queried with `GetAll`, `GetRoleName`, and `GetState`. After phase three, A/B labels are rediscovered and path strings compared. No event identity scoring, document mutation/save, model, or game call is part of this block.

Allocation 030 was stopped separately after two complete first rows because an outer command attempted multiple cases and timed out before case-02 wrote `result.json`. It is not pooled. Allocation 031 changed orchestration only: one formal case per container-tool invocation.

## First measured result

Six fresh sessions completed once each: three control, three selection-transition.

| Gate | control | selection transition |
|---|---:|---:|
| completed | 3/3 | 3/3 |
| visual sequence correct | 3/3 none/none/none | 3/3 A/B/none |
| session `GetAddress` exact match | 3/3 | 3/3 |
| two listener registrations | 3/3 | 3/3 |
| old A/B path probe failures | 0 / 54 calls | 0 / 54 calls |
| final A path unchanged | 3/3 | 3/3 |
| final B path unchanged | 3/3 | 3/3 |
| final keymap empty | 3/3 | 3/3 |

Across all six cases, **108/108 old-path RPC probes succeeded** and there were **0/12 target path identity changes**.

## Interpretation

**Fact:** under this private full-standard-stack fixture, producing verified A/B selection transitions did not make the pre-discovered A/B paths unreadable and did not change their rediscovered paths.

**Inference:** selection transition by itself is insufficient to explain the defunct/reincarnation construction observation in #415. Since Registry, listener registration, launcher-generated bus, session discovery, discovery×listener interaction, and now selection transition have all been insufficient in isolation, the remaining explanation is increasingly an **exact timing/panel churn interaction or a higher-order interaction** rather than a single listed component.

**Boundary:** this does not dispute the #415 construction observation, prove path stability in general, or decide whether AT-SPI events identify selected document objects. It is a path-lifetime ablation only.

## ERROR CHECK

Frozen audit passes all six formal rows. Eight deliberate post-formal corruptions are rejected: task identity, arm assignment, visual state, changed path, failed path probe, held-key claim, listener count, and session-address match. No formal rerun was used. A fresh extraction of the retained evidence bundle is re-audited before publication.

## H / T / D / C / U

**H:** if actual selection-transition/event-production is the missing cause, the candidate should reproducibly make old target paths unreadable or reincarnate while the matched no-transition control remains stable.

**T:** six fresh first sessions, fixed 3+3 schedule, one case per container invocation, same full AT-SPI stack and path probes.

**D:** `REJECT_SELECTION_TRANSITION_ALONE_AS_DEFUNCT_CAUSE_SCOPED` because every frozen gate passes in both arms.

**C:** the original construction may depend on exact ordering/timing of panel creation, accessibility enumeration, selection transitions and event production; a higher-order interaction can exist even when each isolated factor is insufficient.

**U:** one application/version/theme/backend; private chroot isolation; no host PID attribution from the chrooted accessibility bus; small n; no general accessibility identity claim.

## Next single question

Do not duplicate #415's event-identity allocation. If #415 still reproduces path defunct behavior, compare **exact operation ordering/timing** from its construction against this stable transition fixture before adding another semantic mechanism.
