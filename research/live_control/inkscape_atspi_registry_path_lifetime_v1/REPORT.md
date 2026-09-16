# AT-SPI Registry presence vs Inkscape object-path lifetime

Decision: **REJECT_REGISTRY_ALONE_AS_DEFUNCT_CAUSE_SCOPED**.

## Question
Issue #451 isolates one factor suggested by the contrast between the registry-less direct-read work and the standard-stack selection-event construction: is presence of the genuine AT-SPI Registry **by itself** sufficient to make labelled Inkscape object paths become defunct or reincarnate when the Layers and Objects panel is closed and reopened?

## Frozen design
Publication base `d0c667eebc8af0e8c84c8bce86fea1230515a015`. Six fresh sessions, alternating three `no_registry` and three `registry` arms. Both use the same private explicit `AT_SPI_BUS_ADDRESS`, Xvfb/Openbox, unmodified Inkscape and labelled A/B SVG. The registry arm adds only the official `at-spi2-registryd` from retained Debian `at-spi2-core 2.56.2-1+deb13u1` on the same private bus. Neither arm uses the standard bus launcher/session `org.a11y.Bus` or event listener registration.

Each case opens Layers/Objects, dynamically discovers `AI_Target_A` and `AI_Target_B`, probes those paths, closes the panel and probes the old paths again, reopens the panel, rediscovers A/B, and compares paths/names. No document edit/save/effect, model or game call.

Frozen source SHA-256:
- `run_case.py`: `e8f3301b24fa57f6cc012c9da2e8baf7c61fbd9e41d387376aff203d942a015a`
- `native_dbus.py`: `3a6044c2f88d0828f50b5234f61390df46ee5876c1f2046fa802c481b6d3ea1e`
- `audit.py`: `e8d648f1faab82793cc358c3c063c5477db6e4112f3568366b7ef8557c29e51a`
- `prereg.json`: `49a9b40020ca1f9f65b97086c47a8c128966ed174441f1f12c62b07ab879bc57`

## First measured result

| Arm | n | old A/B paths readable while panel closed | reopen path identical | old path resolves original Name after reopen | final keymap empty |
|---|---:|---:|---:|---:|---:|
| no Registry | 3 | 3/3 | 3/3 both A+B | 3/3 both A+B | 3/3 |
| genuine Registry | 3 | 3/3 | 3/3 both A+B | 3/3 both A+B | 3/3 |

The Registry owner was absent in all no-Registry cases and present in all Registry cases. Thus adding the genuine Registry alone did **not** reproduce the defunct/reincarnation behavior reported during #415 standard-stack construction.

## Interpretation
**Fact:** in this explicit-address topology, A/B table-cell object paths remained queryable during panel close and were rediscovered at exactly the same paths/names after reopen in all six sessions.

**Inference:** Registry presence alone is insufficient to explain the difference between the direct-read topology and #415's standard-stack construction. Remaining candidates include bus-launcher/session integration, event-listener registration, timing/panel churn details, or another topology-dependent factor.

**Boundary:** this does not falsify #415's observed defunct paths and does not establish that AT-SPI paths are stable identities in general. It only rejects one proposed causal factor under this fixture.

## ERROR CHECK
`audit.py` independently validates all six rows and returns `REJECT_REGISTRY_ALONE_AS_DEFUNCT_CAUSE_SCOPED` with zero errors. Six post-measurement corruption controls (owner flip, changed path, wrong name, held input, unreadable closed path, unfinished case) are all rejected. They are not additional live samples.

## Construction history
A first attempt to reuse the full standard bus launcher was stopped before app input because `/etc/at-spi2/accessibility.conf` already pointed at another session's working directory. Continuing would have created a shared-global write race. The formal experiment therefore uses isolated explicit-address buses in both arms and starts `at-spi2-registryd` directly in only the Registry arm. Construction also caught a read-only helper allowlist mismatch for `NameHasOwner`; owner verification was moved to `dbus-send` before measurement without changing path queries or panel operations.

## Next single question
Do not take #415's live selection-event lease. If its measured result later confirms path defunct/reincarnation under the complete standard stack, isolate **listener registration / standard bus-launcher integration** as the next one-factor cause rather than assuming Registry presence explains it.
