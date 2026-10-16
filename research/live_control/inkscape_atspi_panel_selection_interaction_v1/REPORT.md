# Inkscape AT-SPI panel-churn × selection interaction on object-path lifetime

Task `INKSCAPE-ATSPI-PANEL-SELECTION-INTERACTION-20260917-033`, Issue #605.

**Decision: `REJECT_PANEL_CHURN_X_SELECTION_INTERACTION_AS_DEFUNCT_CAUSE_SCOPED`.**

## Question

With the full private standard AT-SPI stack fixed, does inserting one Layers/Objects panel close→reopen cycle **before the same A→B→none selection sequence** make pre-discovered labelled A/B AT-SPI paths become unreadable or reincarnate?

This is the next one-variable interaction after separate evidence rejected Registry presence, listener registration, launcher-generated accessibility bus, session discovery, discovery×listener interaction, and selection transition alone as sufficient causes under scoped path-lifetime fixtures.

## Frozen comparison

Both arms use official launcher/session `org.a11y.Bus` discovery, genuine Registry, exactly two listeners (`object:state-changed`, `object:selection-changed`), unmodified Inkscape 1.4 and the same labelled A/B SVG. Both arms execute and independently verify `A→B→none`.

- `selection_no_churn`: matched settling interval; no panel state change.
- `panel_churn_then_selection`: after initial A/B path discovery, close Layers/Objects, probe original A/B paths, reopen it, probe original paths again, then execute A→B→none and probe the same original paths after every phase.

After selection, both arms rediscover A/B labels and compare path strings. No event identity scoring, document edit/save/effect, model, or game call.

Predecessor 032 is retained separately as `STOPPED_ORCHESTRATION_PROTOCOL_VIOLATION` because cases 03/04 were accidentally launched in one container tool call despite the frozen one-case-per-call rule. Allocation 033 changes only task identity/orchestration bookkeeping and executes every formal case in a separate container invocation.

## First measured result

Six fresh first sessions completed once each: three control and three panel-churn candidates.

| Gate | no churn | churn → selection |
|---|---:|---:|
| completed | 3/3 | 3/3 |
| visual A/B/none | 3/3 | 3/3 |
| session GetAddress exact match | 3/3 | 3/3 |
| exactly two listener registrations | 3/3 | 3/3 |
| selection-phase old-path RPC failures | 0 / 54 | 0 / 54 |
| churn close/reopen old-path RPC failures | n/a | 0 / 36 |
| final A path unchanged | 3/3 | 3/3 |
| final B path unchanged | 3/3 | 3/3 |
| final keymap empty | 3/3 | 3/3 |

Overall, **108/108 selection-phase old-path RPC calls succeeded**, **36/36 candidate churn-phase RPC calls succeeded**, and there were **0/12 final target path identity changes**.

## Interpretation

**Fact:** in all three candidates, the original A/B paths remained readable immediately after panel close, immediately after reopen, and after each A/B/none selection phase; final rediscovery returned exactly the original paths.

**Inference:** this specific panel-churn × selection interaction is insufficient to reproduce the #415 construction's defunct/reincarnation observation. With simple named factors and this two-factor interaction failing, the remaining explanation is increasingly tied to **the exact construction ordering/timing/enumeration sequence or a higher-order interaction**.

**Boundary:** this does not falsify #415's construction, prove AT-SPI path stability generally, or decide whether public events carry document selection identity. It is a path-lifetime interaction ablation only.

## ERROR CHECK

Frozen audit passes all six rows. Eight deliberate post-formal corruptions are rejected: task, arm, visual sequence, changed path, failed churn probe, held input, listener count, and session-address mismatch. No formal case was rerun. A fresh extraction of the publication bundle reproduces the same audit decision.

## H / T / D / C / U

**H:** if panel churn and selection transition interact causally, candidate paths should remain stable through churn itself but fail during subsequent selection while controls remain stable.

**T:** six fresh first sessions in the frozen 3+3 order, one case per container invocation, exact same full stack and selection operations; candidate adds only one panel close→reopen cycle.

**D:** `REJECT_PANEL_CHURN_X_SELECTION_INTERACTION_AS_DEFUNCT_CAUSE_SCOPED` because every control and candidate path/readability/visual/session/listener/input gate passes.

**C:** #415 construction may differ in a subtler ordering: panel creation/enumeration while listeners are active, exact delay before selection, target-row defunct events during internal model refresh, or another interaction not represented by one completed close→reopen cycle.

**U:** one Inkscape version/theme/backend, small n, private chroot isolation, no host PID attribution from chrooted accessibility bus, no performance claim, no event-identity claim.

## Next single question

Do not duplicate #415. If its construction/future formal work still shows path defunct behavior, reproduce **its exact operation ordering** against this stable fixture and move only one timing/order boundary at a time.
