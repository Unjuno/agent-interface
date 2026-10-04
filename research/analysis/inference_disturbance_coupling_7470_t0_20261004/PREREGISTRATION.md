# Preregistration — Issue #7470 T0 — 2026-10-04

## H / T / D / C / U

- **H:** Holding inference durations `{1,2,3,4}` and disturbance severities `{0,1,2,3}` exactly fixed, pairing long latency with high severity can increase worst-case state excursion or stale-risk exposure in a declared finite interaction plant relative to the reversed pairing. A null plant with no latency×disturbance term must be invariant across pairings.
- **T:** Enumerate all 24 permutations assigning the four fixed latencies to the fixed event sequence of severities 0,1,2,3. Include explicitly rank-aligned and rank-reversed pairings among those permutations. For each event and plant, the frozen transition is `x' = max(0, x + severity - u + g*latency*severity)`, with `x0=0`, bounded cover action `u=1`, and interaction gain `g=0` for the null and `g=0.25` for the planted interaction. Declared envelope: `x<=6`. Report per-event state trace, event-step count outside envelope, per-event fresh-action availability times, sum of stale-cover occupancy, severity-weighted stale exposure, and total termination/release tick. Calibration is not used; all permutations are enumerated. One candidate invocation, then one independent raw-only audit only if candidate exits 0; retries 0. Auditor mutation controls: changed marginal, missing event, and altered score.
- **D:** `PASS_METHOD_SCOPED` only if every pairing preserves exact latency/severity multisets and total horizon, the no-interaction plant's state/excursion/outside-envelope outcomes are identical across pairings, the aligned interaction plant has strictly greater peak state and stale-risk exposure than the reversed pairing, and an independent audit reconstructs all 48 trajectories and rejects all 3 mutations. Any mismatch is `FAIL_METHOD`; missing provenance is HOLD. No toy result supports a live safety or deployment claim.
- **C:** The transition intentionally plants an interaction term; severity order is fixed and the latency multiset is small. This can establish that the experiment detects its own planted term but cannot show such coupling exists in real systems.
- **U:** No empirical inference distribution, disturbance trace, cover policy, GUI/game, human, model, causal runtime relationship, or safety threshold is validated. The discrete envelope is arbitrary and not a real-system safety boundary.

## Freeze / launch gates

Base main: `0178fd24e9c317fff40e0fa1952fbe7e8ae01078`. Branch: `research/inference-disturbance-coupling-7470-t0-20261004`. Additive path: `research/analysis/inference_disturbance_coupling_7470_t0_20261004/`; formal `results/` must be absent. Candidate/auditor/spec/test identities are pinned in `PRELAUNCH_FREEZE.json`. If main changes, the Issue gains a conflicting owner/allocation, output becomes occupied, or hashes differ before launch, STOP before candidate. Formal candidate and audit each run at most once.

## Environment

Issue #7470 describes a CPU-only standard-library finite simulator and does not require container isolation. This bounded local model has no external effects, so the host Python path is selected; no container, model, GUI, network, GPU, or input is used. No memory or isolation claim is made.
