# Live X11 effect-owner boundary: expected-version binding at side-effect commit

Decision: **PASS_EFFECT_OWNER_BOUNDARY_SCOPED**. Ordinary XTEST input does not carry the plan-time target-incarnation/version precondition into the application effect commit. A cooperative application-owned `effect_if_version` endpoint can reject a stale effect because validation and effect occur in the same owner operation. This is a boundary result, **not** a proposal to replace universal GUI control with app-specific semantic APIs.

Task lineage: Issue #273. Stopped allocation `X11-EFFECT-OWNER-BOUNDARY-20260916-011`; completed successor `...-012`. Publication base `82572e80f81e19fb7129218fb5af4386795d8d8d`.

## One-factor question

Both arms use the same rendered Tk application, initial target A/version 1, a successful status recheck, and the same mutation schedule after recheck. The only effect path differs:

- `xtest`: inject real X11 Space KeyPress/KeyRelease. The application handles it against whatever target incarnation is current when the event arrives.
- `conditional`: call the same application's main-thread `effect_if_version(expected_target_version=1)`. The application compares its current target version and applies the same logical counter effect only on equality.

Ground truth binds the effect to the target incarnation sampled/rechecked before the race. Replacement or ABA incarnation change therefore invalidates the old intent even when the public target label returns to A.

## Frozen design

Before measurement, Issue #273 records prereg SHA-256 `d8314fd6c0ed90cdb16b66987faac59db4e6189dfdfe300b597543fed7f247b0` and measured source hashes. Forty first cases: five repetitions × four trajectories × two arms, shuffled once with `random.Random(26820260916)`.

Trajectories: stable A/v1; replace A/v1→B/v2; ABA A/v1→B/v2→A/v3; and unrelated mutation with target remaining A/v1.

Construction retained two pre-input Xauthority failures. Final construction used private Xvfb `-ac` plus explicit empty Xauthority for both controller and child app and passed stable/replace × both arms.

Allocation 011 hit the outer tool budget after six complete cases, with no seventh result file. Those results are retained separately and are not pooled. Allocation 012 changed orchestration only: the exact 40-case schedule is partitioned into fixed groups of at most four fresh Xvfb/application processes. Its prereg SHA-256 is `d4c6b68d1947128f3fee16a5a20f7f0a0fca7c8de7198fc8e311e58b971fa70d`. Correctness, not timing, is the promotion endpoint.

## First measured result — allocation 012

| Trajectory | XTEST | Cooperative effect owner |
|---|---:|---:|
| stable A/v1 | 5/5 correct; effect A/v1 | 5/5 correct; effect A/v1 |
| unrelated mutation | 5/5 correct; effect A/v1 | 5/5 correct; effect A/v1 |
| A/v1 → B/v2 | **0/5 correct; 5/5 wrong-target effects on B/v2** | **5/5 correct; 5/5 rejected, zero effects** |
| A/v1 → B/v2 → A/v3 | **0/5 correct; 5/5 wrong-incarnation effects on A/v3** | **5/5 correct; 5/5 rejected, zero effects** |

All 40 application processes exited normally, every XTEST case ended with an empty physical keymap, and no case produced more than one effect.

The XTEST result is not a failure of XTEST delivery: it delivered exactly the requested key. The failure is semantic binding. A key event has no field carrying `expected_target_version=1`, so once the application has moved to B/v2 or a new A/v3 incarnation, generic input is interpreted in the new context.

The cooperative arm succeeds by adding privileged application semantics. Therefore it demonstrates **where** a coherent commit boundary can exist; it does not supply a universal GUI implementation of that boundary.

## Descriptive timing — not a promoted comparison

The two effect paths have different IPC/input mechanisms, and allocation 012 deliberately groups cases in parallel after 011's orchestration timeout. Timing is retained only diagnostically. Audit summary median effect round-trip was about 69.740 ms for XTEST and 4.228 ms for the cooperative endpoint, but these values are **not comparable task-speed evidence** and do not justify a performance claim.

## Interpretation

**Fact:** after a successful pre-effect recheck, a relevant target incarnation changed. Generic XTEST subsequently produced ten stale/wrong-incarnation effects across replace+ABA; the app-owned conditional operation produced zero.

**Inference:** an external GUI input broker cannot in general make an application's semantic state check and application effect one atomic operation unless the effect owner exposes a suitable commit-time contract or the GUI itself naturally rejects stale context. Another fresh check before XTEST narrows but cannot eliminate the check-to-effect interval.

**Boundary:** the app-owned endpoint is exactly the kind of privileged application action API that the universal Agent Interface cannot assume for arbitrary software. The result therefore supports fail-closed/yield semantics when no authoritative effect-owner boundary exists; it does not justify adding app-specific APIs to the universal controller.

## ERROR CHECK

The frozen independent audit re-derives ground truth from trajectory/arm, checks target-version progression, effect rows, physical key emptiness, process exit and one-effect maximum. Allocation 012 audit returns `PASS_AUDIT` for all 40 cases. Five post-measurement corruption controls are rejected; they add no live samples.

Final audit SHA-256: `1a10a1343dfb893b3730548b1f77840958145af8a1e41b348cd4e7e29a7d3f58`.

## H / T / D / C / U

**H:** generic XTEST cannot bind an expected application target incarnation at effect commit; an effect-owner conditional operation can.

**T:** 40 frozen live-X11 cases in a rendered synthetic application; real XTEST in one arm, cooperative same-app commit endpoint in the other. No model/game calls.

**D:** all preregistered correctness gates pass. Retain `PASS_EFFECT_OWNER_BOUNDARY_SCOPED` as a boundary/generalization result, not a production mechanism.

**C:** many real applications already disable invalid actions or route input based on current focus/state, which may reduce stale effects without a custom endpoint. Conversely, they may expose no authoritative incarnation token at all.

**U:** one cooperative Tk fixture, no model, no arbitrary application, no OS-level semantic transaction, no proof about Windows/macOS/accessibility APIs, no task-speed claim.

## Next single question

Do **not** build another synthetic commit protocol. Transfer the negative boundary to one existing ordinary application path: identify a real action whose target/context can change between final revalidation and OS input, then determine whether the application itself rejects the stale input or applies it to the new context. If no authoritative commit-time identity is observable, retain that as `DEPENDENCY_UNAVAILABLE` rather than inventing atomicity.
