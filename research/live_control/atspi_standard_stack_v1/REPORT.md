# Standard AT-SPI Registry/event positive control

Decision: **PASS_STANDARD_ATSPI_EVENT_POSITIVE_CONTROL**. A genuine version-matched AT-SPI stack with `org.a11y.Bus`, the upstream Registry daemon, and a formally registered event listener delivered standard `object:state-changed:focused` events from unmodified Inkscape in all three frozen fresh sessions. This repairs the transport/control prerequisite only; it does **not** establish document-object selection identity.

Issue #389; task `ATSPI-STANDARD-STACK-20260916-022`; publication BASE `ae2e940c958dbecddcb253ae93b65513d7fa03be`. No shared runtime or application code changed.

## Provenance and intervention

The local container had no usable external TCP/DNS, so package acquisition used a branch-only GitHub Actions packaging workflow. Run `35092146916`, artifact `10445045033`, artifact digest `sha256:4c50f92c2481ccbb3f4d96c0d93b4c1635a41d2ad1fe4ec778d749e9adc67ccd` produced exact Debian `at-spi2-core 2.56.2-1+deb13u1 amd64`. Package SHA-256: `135b9619d7f8bf8996adcee7a869af2563184faaa7eae8f1e384ede62846252f`. The package was extracted into a private directory, never installed globally.

Official binary SHA-256: `at-spi-bus-launcher` `dfa902734ac9adea3044dd1cd0f23164bff8bfb681bfc55be491f125c55faa31`; `at-spi2-registryd` `428c3a6d074b50748f2a74ec61ef6b0ae0816c450c9447577d610ef903137694`. GNOME upstream tag `2.56.2` resolves to commit `71b07959873a371a4f2e6e3874dba9777e8e2776`. No fake registry/service implementation was used.

A private session D-Bus started official `at-spi-bus-launcher`, which created the accessibility bus. The official Registry daemon was activated from a private service directory. The runner registered `object:state-changed:focused`, launched unmodified Inkscape through the normal session `org.a11y.Bus` path (no explicit `AT_SPI_BUS_ADDRESS` for the application), dynamically PID-bound the Inkscape accessibility destination, and independently located a named public button advertising Action.

## Construction retained

Construction failures occurred before the measured freeze and are retained: (1) Python-Xlib did not see the subprocess-only DISPLAY/XAUTHORITY environment; (2) an event-body regex double-escaped whitespace/newline and falsely counted zero operation events even though raw monitor data contained them; (3) after fixing strings, int32 detail parsing remained double-escaped. The final construction passed owners, Registry, listener, known widget, event, unchanged-SVG and key-release gates. No measured source changed after the freeze posted to #389.

## Frozen measurement

Exactly three fresh serial sessions, displays 430/431/432. Each required session `org.a11y.Bus` owner, Registry owner, persistent listener registration, a named public button with Action, then only `Alt+f`, Down, Escape. Events were accepted only inside operation-start -50 ms through operation-end +200 ms and only if the sender equalled the accessibility bus name independently mapped to the spawned Inkscape PID. No edit/save/effect, model or game call.

| Endpoint | case-00 | case-01 | case-02 |
|---|---:|---:|---:|
| `org.a11y.Bus` owner | PASS | PASS | PASS |
| Registry owner | PASS | PASS | PASS |
| listener registered | PASS | PASS | PASS |
| named public widget | PASS | PASS | PASS |
| PID-attributed focused events in operation window | 4 | 4 | 4 |
| SVG unchanged | PASS | PASS | PASS |
| final keymap empty | PASS | PASS | PASS |

All three discovered `Reset to simple snapping mode` as a named button exposing `org.a11y.atspi.Action`. All operation-window events were standard `org.a11y.atspi.Event.Object.StateChanged` with detail `focused` from the PID-bound Inkscape sender.

## Interpretation

**Fact:** with the genuine Registry/event-listener stack present, the same Inkscape environment yields process-attributed standard accessibility events.

**Inference:** the zero-event result in #376 is attributable to the tested registry-less explicit-address topology, not evidence that Inkscape generally emits no AT-SPI events.

**Boundary:** this positive control validates event transport and listener registration only. It does not say that A/B document selection emits an identifying event. That is the next separate question.

## ERROR CHECK

Frozen independent audit returns `PASS_STANDARD_ATSPI_EVENT_POSITIVE_CONTROL`. Seven post-measurement corruptions are rejected: missing Registry, missing event, wrong sender, missing widget control, SVG change, held key and wrong package identity. The auditor imports neither the runner nor bus client.

## H / T / D / C / U

H: a real standard AT-SPI stack restores positive event transport absent from the registry-less topology.
T: three frozen fresh sessions with an ordinary-widget control and benign focus operation.
D: PASS. Retain standard event transport as available in this private full-stack fixture.
C: event availability does not imply useful document-object identity; menu/focus events may be much richer than canvas selection semantics.
U: one Inkscape/build/host and private desktop stack; no production/autostart claim, no selection-event claim, no performance claim.

## Evidence boundaries

Measured source hashes are frozen in Issue #389 comment `5697051607`. Full local evidence archive: `atspi_standard_stack_v1_complete.tar.gz`, SHA-256 `a8d022f62876bf0bc56e502297b3d1251f54a0ea9ae6ab28411bc326f829b27b`. Compact package SHA-256 `3f2b61567235ef77abf4522319025de07a1649d6802f5bdf6cd4a163f7b6707b`. The branch-only package-acquisition workflow is deliberately excluded from the final research PR.

## Next single question

Keep this exact standard stack/listener transport fixed. In a separately frozen block, establish none/A/B canvas selection from independent visual evidence and test whether standard selection/state/focus events identify the affected document object. Do not change transport, add app-specific APIs, or add new screenshot thresholds in that rung.
