# AT-SPI listener registration vs Inkscape object-path lifetime

Decision: **REJECT_LISTENER_REGISTRATION_ALONE_AS_DEFUNCT_CAUSE_SCOPED**.

## Question
After Issue #451 showed that genuine Registry presence alone does not reproduce the defunct/reincarnation behavior seen during #415 construction, this rung holds Registry presence fixed and changes only event-listener registration.

Both arms use the same private explicit `AT_SPI_BUS_ADDRESS`, genuine official `at-spi2-registryd`, Xvfb/Openbox, unmodified Inkscape, labelled `AI_Target_A/B` SVG and identical Layers/Objects close/reopen probes. The candidate additionally registers exactly `object:state-changed` and `object:selection-changed`, matching the listener-family shape used in #415 construction. Neither arm uses the standard session `org.a11y.Bus` launcher topology.

## Frozen design
Publication base `2c89154561fdf387f63463ded1bed171a6ce8352`, Issue #460. Six fresh first sessions: `no_listener, listener` alternating three times. No retry/replacement/tuning after outcome.

Frozen SHA-256:
- `run_case.py`: `ca18ecf7b7e739b4bf4178eafe047312000c2f0ad212b0e81d7c88a1bf158945`
- `native_dbus.py`: `3a6044c2f88d0828f50b5234f61390df46ee5876c1f2046fa802c481b6d3ea1e`
- `register_listener.py`: `1641aea9774cefa3ba1a94059cf26d7828b0a1e38db1c88be5ce5b73be4e7234`
- `audit.py`: `2ec13f01b7a44d98c33573dae7c26e5b0984016fa21c07ed2edcf3d3f6df401f`
- `prereg.json`: `63a817384960be1f687b904dffb15be1a32c4751a50dfb554a9a2a6ea5f7f889`

## First measured result

| arm | n | Registry owner | listener registrations | old A/B readable while closed | reopened A/B path identical | old path name preserved | final keymap empty |
|---|---:|---:|---:|---:|---:|---:|---:|
| no listener | 3 | 3/3 | 0 | 3/3 | 3/3 | 3/3 | 3/3 |
| listener | 3 | 3/3 | 2 per case, all registered | 3/3 | 3/3 | 3/3 | 3/3 |

`GetAll`, `GetRoleName`, and `GetState` all returned successfully on both old target paths while the panel was closed in every case. After reopen the target labels were rediscovered at the same paths and the old paths still resolved `AI_Target_A/B`.

## Interpretation
**Fact:** adding the two event-listener registrations did not change the measured object-path lifetime under this explicit-address private-bus topology.

**Inference:** listener registration alone is insufficient to explain #415 construction's defunct-path behavior. Combined standard bus-launcher/session integration, timing/panel churn, or another topology interaction remains unresolved.

**Boundary:** this does not contradict #415's observation and does not establish stable AT-SPI identity in general. The experiment deliberately does not take #415's selection-event identity allocation.

## ERROR CHECK
The frozen audit reports six valid rows, three per arm, and zero errors. Six post-measurement synthetic corruptions are rejected: listener-count change, Registry-owner change, path change, wrong old-path name, held-input claim, and unreadable closed path. They are audit controls, not additional live samples.

Construction consisted of one excluded case per arm and matched the formal behavior. No shared `/etc/at-spi2/accessibility.conf` mutation was used.

## Next single question
Wait for #415's formal result. If full standard-stack measurement again shows target paths becoming defunct, the next one-factor cause should be **standard bus-launcher/session integration** (or exact panel/timing sequence), since Registry-alone and listener-registration-alone have now both failed to reproduce it in isolation.
