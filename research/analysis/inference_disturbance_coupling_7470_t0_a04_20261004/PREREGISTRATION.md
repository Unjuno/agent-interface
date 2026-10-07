# Preregistration — INFERENCE-DISTURBANCE-COUPLING-7470-T0-20261004-A04

- **H:** Under four intact circular phase shifts, explicitly simulating two complete periods (including last-to-first seam transition) preserves null invariance and yields phase-dependent planted-interaction outcomes.
- **T:** Enumerate four unique latency rotations against the fixed disturbance period, repeat both resulting streams for two periods, and independently reconstruct all eight trajectories (four shifts × two plants), each containing eight events. Report per-shift centered Pearson cross-correlation and all event rows, including seam rows.
- **D:** `PASS_METHOD_SCOPED` only if exact shifts and fixed marginals/horizon hold, each trajectory contains both period boundaries, null is phase invariant, planted outcomes vary by phase, raw reconstruction agrees, and 3/3 mutations are rejected.
- **C:** This remains a tiny artificial periodic process and planted interaction; the finite wrap seam is not a real runtime boundary distribution.
- **U:** No real coupling, prevalence, causal runtime effect, GUI/game, human benefit, safety, or deployment threshold is established.

Output absent; one candidate invocation and one auditor only after candidate exit 0; zero retries. Candidate, auditor, spec and test hashes pinned in PRELAUNCH_FREEZE.json. Host-only CPython standard library; no external effects.
