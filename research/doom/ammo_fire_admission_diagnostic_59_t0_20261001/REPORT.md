# Retained MAP01 ammo/fire diagnostic — Issue #59 T0

## H / T / D / C / U

- **H:** Completed `space`-declared hold steps with positive pre-step typed ammo show an in-loop sampled ammo decrease in a greater share of v39 than v38. A step that does not reach the exact declared `keys_held` set is not a confirmed firing step.
- **T:** One source-frozen, read-only computation over the canonical v38 and v39 runtime event logs; each submitted/started `space` step was joined to ordered per-key admission and the exact keyset marker. Pre-step ammo was the latest typed sample at/before `step_started`. For a completed step, the final same-step observation before `step_completed` was excluded as post-release; earlier observation rows were joined to typed ammo by exact sequence and capture timestamp. A separate process independently recomputed the rows and contrasts from the raw logs.
- **D:** **`PASS_DIAGNOSTIC_CONTRAST_SCOPED`**, independent audit **`PASS_AMMO_FIRE_RAW_AUDIT`**, zero errors. v38: one started/one completed keyset-confirmed space hold, source ammo 48, in-loop value `[48]`, decrease fraction **0/1 = 0.0**. v39: eleven started space holds; nine completed with the exact admitted/held keyset, one interrupted after the keyset, and one partial/unconfirmed step with no `keys_held` marker. All observed source ammo values were positive. Of the nine completed v39 steps, **9/9** had at least one in-loop typed ammo value below the pre-step value, decrease fraction **1.0**. The completed-step contrast is +1.0 in this small descriptive fraction.
- **C:** These are two unmatched stochastic episodes, with different policies, exposure and action schedules. A HUD ammo decrement temporally inside a declared attack-step envelope does not identify which shot caused it, prove a target hit, or distinguish a beneficial shot from a wasteful one. Incomplete/interrupted steps were excluded rather than imputed. The partial step `cover-4:10` requested `Down + space` but did not produce a complete keyset marker; it is not counted as a confirmed attack.
- **U:** No estimate of tactical quality, target hit, kill attribution, survival benefit, task completion, causal effect, live-controller robustness, latency benefit, speedup, or human-tempo equivalence. This does not satisfy Issue #59's live threat-control gate.

## Reproducibility

- Frozen main: `4b7fe7837e4ee8c0d035ebfbf52baf014f042295`; freeze/source commit: `02b6965b2d20e50098cbdf6d1b3ced887f4a12dd`.
- Python: CPython 3.14.5, standard library only. Host-only execution; no shared container/GPU/OrbStack resource was used.
- Candidate invocation: once, exit 0. Independent raw-only auditor: once, exit 0.
- Six TDD construction/negative-control tests pass. The test matrix ensures post-release ammo cannot enter the in-loop set, future samples cannot become the source observation, and a partial multikey admission is not counted as completed firing.
- v38 inputs: event SHA-256 `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3`; report SHA-256 `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58`.
- v39 inputs: event SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`; report SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`.
- Candidate raw SHA-256 `554361beb7e5991b88aa3d83aad2f8e889c5921aa6a3a48317e0b8292591b14a`.
- Independent audit raw SHA-256 `b587d1afae59f6868366faedbafe7299768a279669dd0a5587e2af0e9fbc8041`.

## Disposition

This is a narrow retained-trace diagnostic for Issue #59's ammunition-aware fire-behavior inventory. It establishes that v39's completed declared attack holds more often coincide with an observed ammo-counter decrease than v38's sole short attack hold. It does not establish that this pattern improved combat or was intentional. Preserve the first episodes and their scores unchanged; use a separately frozen, owner-authorized live allocation for any future policy/effect question.
