# Inkscape AT-SPI event-route boundary under explicit-address topology

Decision: **DEPENDENCY_UNAVAILABLE_ATSPI_EVENT_ROUTE_SCOPED**.

Task: `INKSCAPE-ATSPI-EVENT-ROUTE-20260916-021`, Issue #376. Frozen publication base `8d987773ca090640822f96b0710e6c7872eabdfd`.

## Question

The predecessor #362 found that queried AT-SPI snapshot fields did not distinguish none/A/B document-object selection. This rung changes one factor only: keep the same explicit `AT_SPI_BUS_ADDRESS` topology and passively monitor the accessibility D-Bus for standard `org.a11y.atspi.Event.*` signals during verified selection/focus transitions.

This is **not** restoration of the missing standard AT-SPI registry/autolaunch stack and does not use a fake registry or private Inkscape semantic API.

## Frozen sources

- `run_case.py`: `2d1411c85047be096a9aab2df729dd9761b76d3447e71ef319ed5c53639a7740`
- `native_dbus.py`: `3a6044c2f88d0828f50b5234f61390df46ee5876c1f2046fa802c481b6d3ea1e`
- `audit.py`: `4f86f9eb83a97b6572d3a83f4accf2cabffcda952b3eeda0dfb4f349f91d850d`
- `prereg.json`: `1ff2eea650be735ec62496b8ab37dc338a4ea009b9937f5ebf1c7bde3707181f`

Construction before freeze used both app-sender-filtered and whole-bus passive monitors. Both saw zero standard AT-SPI Event signals during A selection, B selection, clear, and Inkscape focus out/in, while receiving D-Bus monitor-control traffic. Construction is excluded from measurement.

## Measured allocation

Four fresh private D-Bus/Xvfb/Inkscape sessions, one case per outer invocation. Each case monitored five phases: idle, select A, select B, clear, and Inkscape focus out/in via a temporary xterm. Selection phases were independently verified from screenshot handles. The spawned Inkscape PID was resolved to its accessibility-bus destination. SVG bytes and final input state were checked.

| Endpoint | Result |
|---|---:|
| `org.a11y.atspi.Registry` owner present | **0/4** |
| none → A → B → none visual transitions correct | **4/4** |
| focus out/in completed | **4/4** |
| standard `org.a11y.atspi.Event.*` signals across 20 phases | **0** |
| D-Bus monitor-control signals | **40** |
| SVG unchanged | **4/4** |
| final key/button state empty | **4/4** |

The monitor controls show that passive observation was attached to the bus, but they are not a positive AT-SPI-event control. Because the standard Registry service is absent, the normal event-listener registration path is unavailable. Therefore zero observed AT-SPI events is classified as a **dependency/transport gap**, not as proof that Inkscape emits no events under a complete desktop accessibility stack.

## ERROR CHECK

Independent audit result: `PASS_ATSPI_EVENT_ROUTE_UNAVAILABLE_AUDIT`, 4 rows, 0 errors, 0 AT-SPI Event signals, 40 monitor controls. Seven post-measurement corruption controls were rejected: invented event, forged registry presence, erased monitor control, wrong visual selection, SVG mutation, held key, and missing case.

## H / T / D / C / U

**H:** a public AT-SPI event stream may carry object-identifying state/selection/focus changes even when snapshot fields are non-discriminative.

**T:** four fresh sessions × five passive monitor phases, with verified visual selection/focus transitions. No edit/save/effect/model/game call.

**D:** retain `DEPENDENCY_UNAVAILABLE_ATSPI_EVENT_ROUTE_SCOPED` for this explicit-address, registry-less topology.

**C:** a complete `at-spi2-core` registry/event-listener stack may cause the bridge to route standard events; passive monitoring without that registry is not equivalent to the normal listener lifecycle.

**U:** one Inkscape version/backend, small sample, explicit-address topology. No conclusion about full-stack AT-SPI events, other accessibility platforms, or other apps.

## Retention

Compact outcome archive: 294,452 bytes, SHA-256 `85818edee4439d743ab5f1e5e8dad2f5bd728d3f3648fa49b85c772ffe634dde`.

Full conversation archive: 2,341,128 bytes, SHA-256 `a888945ea30aabb752df6910c7d81c453019a6c49e130d08fcf899b2fd5dc40c`.

The full archive additionally retains construction and process logs. GitHub retention boundaries are stated explicitly rather than treating absent bulk raw as retained.

## Next single question

Do not add another screenshot heuristic. The next step is environmental: materialize a real standard AT-SPI Registry/event-listener stack and first obtain a positive standard event control. Only then test document-selection events. If that stack cannot be reproduced, keep the event dependency unavailable and move to another public semantic source/domain rather than simulating a private application API.
