# AT-SPI selection path criterion audit

Decision: **HOLD**. This independent audit did not reproduce the construction-only contradiction inside the preregistered A-selection operation window, so it does not reject Issue #415's path-equality criterion. It also does not validate that criterion as sufficient selection identity.

Task `ATSPI-SELECTION-PATH-CRITERION-AUDIT-20260916-024`, Issue #432. Frozen publication base `9558313ed704804031733031f9e9443ddffc54de`.

## Question
Issue #415 currently allows direct target identity when an event source path equals a dynamically discovered A/B target-cell path. A construction probe found both A and B paths emitting `PropertyChange`/`StateChanged(defunct)` around an A-only canvas selection. This audit asked whether that contradiction occurs inside a predeclared A-selection operation window in fresh sessions.

## Frozen design
Exactly three fresh standard-stack Xvfb/Inkscape sessions. The official privately extracted Debian `at-spi2-core 2.56.2-1+deb13u1 amd64` from #389 was reused. In each case the runner dynamically rediscovered labelled A/B rows, clicked only A, independently verified A-only selection from four-sided handles, retained all PID-bound standard Object events in the A-selection window, and checked empty final key state. No B selection, document edit/save/effect, model or game call.

Frozen source hashes are recorded in Issue #432. Promotion rule required A and B source-path events in all 3 cases, yielding contradictory `{A,B}` under the current criterion. Otherwise HOLD.

## First measured result
All three first outcomes completed; none were retried or replaced.

| endpoint | result |
|---|---:|
| visually verified A-only selection | 3/3 |
| final keymap empty | 3/3 |
| PID-bound Object events in operation window | 394 / 373 / 394 |
| events whose source equals discovered A path | 0/3 cases |
| events whose source equals discovered B path | 0/3 cases |
| exact `AI_Target_A/B` payload events | 0/3 cases |
| current criterion identities from those branches | empty in 3/3 |
| contradictory `{A,B}` identity | 0/3 |

Decision: **HOLD**.

## Construction vs measurement
The retained construction probe did observe four events from each old A/B path around one A selection: `PropertyChange(renderer)`, `StateChanged(defunct)`, `PropertyChange(widget)`, and `PropertyChange(accessible-parent)`. The paths remained readable and retained their names. A no-selection construction also observed 7,902 Object signals with zero exact A/B label payload events.

The frozen measured windows did **not** reproduce those target-path events. Posthoc inspection confirms the same A/B paths do occur elsewhere in each raw monitor stream, but outside the preregistered selection window. No window widening or timing retuning is performed after outcome.

Therefore construction establishes that target-row paths can emit non-selection churn events, while measured evidence says the preregistered A-selection window did not capture them in these three sessions. This is a timing/provenance boundary, not evidence that path equality is universally safe.

## ERROR CHECK
The independent audit requires three rows, A-only visual selection, empty final key state, and preregistered A/B-path contradiction. It returns HOLD because the contradiction gate is not met. Raw `dbus-monitor` streams, selected-A screenshots, exact sources/preregistration, official package provenance reference, and first result files are retained in the conversation evidence archive.

## H / T / D / C / U
**H:** pre-discovered target-row source-path equality can be falsely interpreted as A/B selection identity if unrelated row churn occurs inside the selection window.

**T:** three fresh standard-stack sessions, A-only selection, frozen event families/window/criterion.

**D:** HOLD: 0/3 target-path event cases inside the declared window. Do not reject or promote the #415 criterion from this block.

**C:** the construction contradiction may be caused by row rebuild timing just before/after the measured selection window; #415's own panel churn may differ. A source path can also be non-semantic even if it does appear during a window.

**U:** one Inkscape version/theme/backend, three sessions, fixture labels, exact timing window. This does not prove path equality is a sound semantic identity primitive.

## Successor guidance
Do not open another live allocation that competes with #415. The useful handoff is: retain strict operation-window provenance; if #415 observes a path-equality identity, also report event member/detail and whether the source still resolves to the expected target at the event boundary. Do not broaden the window after outcome to rescue either direction.
