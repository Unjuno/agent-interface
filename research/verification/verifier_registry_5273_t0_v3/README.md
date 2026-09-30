# Verifier registry T0 v3 successor

Review-driven successor to v1/v2; both earlier paths and outcomes remain untouched. V3 evaluates every assignment for every #5268 IR check as one plan, reports per-check and aggregate status, and rejects missing/duplicate assignments. Its raw-only auditor imports neither candidate nor test oracle, independently checks fixture IR shape, requires exact raw/plan/decision field sets and one-to-one case/check identities, and records raw/freeze/auditor digests.

The retained run is host construction only. `run_formal.py` is single-use and writes a fresh result directory; do not rerun or regenerate the freeze over retained evidence. A future run requires a new allocation/path and, for a formal result, an exact shared-container lease before invocation.

Costs are synthetic estimates, never measured latency. Numeric #5268 deadlines have no general unit qualification; these fixtures explicitly assume milliseconds, following the bounded profile convention used in #5269. No scheduler or runtime claim follows.
