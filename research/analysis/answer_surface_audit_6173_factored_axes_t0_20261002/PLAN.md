# Issue #6173 T0-03 — factor attempt, acquisition, and coverage

Allocation: 6173-T0-FACTORED-ACCESS-AXES-03.

## H / T / D / C / U

- **H:** A three-axis record for evaluation-target attempt, byte acquisition/denial, and monitor coverage preserves distinctions that a single run disposition necessarily collapses, while retaining a conservative derived disposition.
- **T:** Freeze a fresh 17-case synthetic event table, including complete and incomplete no-attempt, denied request with/without coverage gaps, direct/derivative returned bytes, missing/partial/misbound response, allowed task/docs, unknown route/recipient, mixed accesses, and contradictory self-claims. Candidate uses only candidate-visible event projections. A raw-only auditor independently reconstructs all three axes from observer-side events and checks candidate/input/observer joins. Run construction tests, candidate once, then independent audit once; host CPU only.
- **D:** PASS_METHOD_SCOPED iff all 17 attempt/acquisition/coverage axes and derived dispositions match; a denied request remains visible even with a coverage gap; missing response or recipient binding cannot become no-acquisition/clean; complete no-attempt is distinct from no-attempt with a coverage gap; self-claims are ignored; mutation controls for event deletion, axis collapse, and forged disposition fail closed.
- **C:** Synthetic event sources are complete only within the declared fixture; real routes/providers/caches can be absent from external logs and semantic derivatives can evade lineage tracking.
- **U:** This is finite method evidence only, not real benchmark monitoring completeness or a contamination finding. No model, user data, private answer, network, app, or GUI. No container is launched while another lane's OrbStack container is active; no existing container is touched.

This is a distinct successor to the flat-label T0/T0b/T0-02 results. Those predecessor outputs remain immutable. Frozen source main is re-read immediately before allocation; this plan does not authorize use of the shared Docker/OrbStack slot.
