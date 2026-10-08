# AT-SPI session-discovery × listener interaction on Inkscape path lifetime

Task `INKSCAPE-ATSPI-DISCOVERY-LISTENER-INTERACTION-20260916-030`, Issue #521.

**Decision: `REJECT_SESSION_DISCOVERY_X_LISTENER_INTERACTION_AS_DEFUNCT_CAUSE_SCOPED`.**

## H
After Registry-alone, listener-alone, launcher-bus-alone, and session-discovery-alone each failed to reproduce #415 construction's target-path defunct/reincarnation, the remaining simple explanation was an interaction between app-side session discovery and listener registration.

## T
2×2 factorial with official launcher/session/Registry held fixed: explicit vs session address mode × no listener vs two registered listener families (`object:state-changed`, `object:selection-changed`). Three fresh first sessions per cell, 12 total. Same labelled A/B SVG, same Layers/Objects close/reopen probes. No selection transitions, event-content scoring, document effect, model, or game calls.

029 was stopped separately by the outer execution limit after two complete first outcomes and two partial no-result cases; 029 is never pooled. 030 changes only task identity plus one-case-per-outer-invocation orchestration.

## First measured result

| cell | path/readability/name/input gate | listener registrations | address mode |
|---|---:|---:|---|
| explicit + no listener | 3/3 | 0 | env present 3/3 |
| explicit + listener | 3/3 | 2 successful/case | env present 3/3 |
| session + no listener | 3/3 | 0 | env absent 3/3 |
| session + listener | **3/3** | **2 successful/case** | **env absent 3/3** |

All old A/B paths were readable through `GetAll`, `GetRoleName`, and `GetState` while the panel was closed, rediscovered at identical paths after reopen, and still resolved `AI_Target_A/B`. Final keymap empty 12/12.

## D
The preregistered interaction was not observed. Session discovery + listener registration together are insufficient under this fixture to explain #415 construction's defunct-path behavior.

## C
Remaining explanations include the exact #415 panel/selection timing/churn sequence, interaction with actual selection transitions/event production rather than listener registration alone, or another standard-stack state transition absent from this close/reopen fixture.

## U
One Inkscape 1.4/Xvfb/backend fixture. Private chroot/session/accessibility buses. PID attribution is unavailable on the chrooted accessibility D-Bus; the unique public `org.inkscape.Inkscape` root on the per-case bus is used only for this path-lifetime fixture. No claim that AT-SPI object paths are stable semantic identities in general.

## ERROR CHECK
Frozen source hashes match the premeasurement freeze exactly. Frozen audit passes 12/12. Eight direct corruptions are rejected: wrong arm, wrong env mode, listener count, changed path, closed-probe failure, wrong old Name, held input, and mismatched session GetAddress witness. Fresh archive extraction reruns the same frozen audit before publication.
