# Inkscape AT-SPI session discovery vs object-path lifetime

Decision: **REJECT_SESSION_DISCOVERY_ALONE_AS_DEFUNCT_CAUSE_SCOPED**.

## Question
With the same official `at-spi-bus-launcher`-generated accessibility bus, Registry, private session bus, fixture and panel operations held fixed, does changing only how unmodified Inkscape obtains the bus address (`AT_SPI_BUS_ADDRESS` vs session `org.a11y.Bus.GetAddress`) reproduce the target-path defunct/reincarnation seen in #415 construction?

## Frozen design
Publication base `8f08418c71a0a8919dd70b0b762cbae99a239bed`, Issue #505. Six fresh first sessions in frozen order: explicit, session, session, explicit, explicit, session. No retry/replacement/tuning. Private chroot avoids shared `/etc` writes. A long private `XDG_RUNTIME_DIR` activates the launcher's upstream abstract-socket fallback; per-case accessibility config names the abstract socket uniquely.

Frozen SHA-256: run_case `308e48c0ae7e628e8470ff2edd31be050a840882f2a3a05f3a1804cde5ee502d`; native_dbus `3a6044c2f88d0828f50b5234f61390df46ee5876c1f2046fa802c481b6d3ea1e`; audit `9e993da0e1bd174a6874fcd782b56841e1de3d21aa672314a7d643f618cad9b2`; prereg `4daeb16832a4a7245a3bf80b471eed12cb07d304b0b4284674df083e923a5e74`.

## First measured result
| Arm | n | address mode gate | old A/B readable while closed | reopen same paths/names | final input empty |
|---|---:|---:|---:|---:|---:|
| explicit address | 3 | 3/3 `AT_SPI_BUS_ADDRESS` present | 3/3 | 3/3 | 3/3 |
| session discovery | 3 | 3/3 env absent + `org.a11y.Bus.GetAddress` rc0 and exact address | 3/3 | 3/3 | 3/3 |

All 6 had Registry owner present. All 12 old A/B paths were queryable through `GetAll`, `GetRoleName`, and `GetState` while the panel was closed. Reopen rediscovered exactly the same paths; old paths still named `AI_Target_A/B`.

## Interpretation
**Fact:** app-side session discovery alone did not change path lifetime in this isolated full-launcher fixture.

**Inference:** together with #451, #460 and #488, Registry presence alone, listener registration alone, launcher-generated accessibility-bus lifecycle/config alone, and app-side session discovery alone are each insufficient in isolation. The remaining #415 construction difference is more likely an interaction, exact timing/panel churn sequence, or another full-stack detail rather than one of these single factors.

**Boundary:** this does not assert AT-SPI paths are stable semantic identities; it does not test selection-event identity. The chrooted accessibility daemon cannot read host `/proc`, so PID attribution is unavailable and the private-bus unique public root Name is used only within this fixture.

## ERROR CHECK
Original frozen audit passed all six rows. Post-formal review found the original audit checked `GetAddress` rc=0 but did not explicitly assert the returned string equals the launcher-reported address. Raw data were not changed. `audit_v2.py` adds only that preregistered hard gate and also passes all six rows. A targeted mismatched-address corruption is rejected by v2. Six other corruptions (arm, env mode, GetAddress rc, changed path, closed-probe failure, held input) are rejected by the original audit.

## Construction history
Early construction attempts retained setup-only failures: config-listen edits did not control the launcher's filesystem socket; upstream source inspection showed socket naming is derived from `XDG_RUNTIME_DIR/at-spi/bus$DISPLAY`, with an abstract fallback when the path would be too long. Construction then succeeded with private abstract sockets. Outer execution limits cut two sequential construction invocations after complete first cases; completed construction outcomes were not used as measured rows.

## H / T / D / C / U
**H:** session `org.a11y.Bus` discovery may be the missing factor causing target-path lifetime changes.
**T:** six frozen fresh sessions; one factor only; first outcomes retained.
**D:** `REJECT_SESSION_DISCOVERY_ALONE_AS_DEFUNCT_CAUSE_SCOPED`.
**C:** #415's defunct observation may depend on interaction among listener/event churn, panel timing, startup order, or another state transition not reproduced by close/reopen alone.
**U:** one Inkscape 1.4/Xvfb/backend fixture; private chroot shims; no PID attribution on the chrooted accessibility bus; no semantic selection claim.

## Next single question
Do not duplicate #415. If #415 formal measurement confirms path defunct/reincarnation, reproduce the **exact #415 panel/selection timing sequence** under the now-isolated session-discovery stack, changing timing/churn sequence only. If #415 does not reproduce defunct paths, retain the construction observation as non-stable and stop this cause ladder.
