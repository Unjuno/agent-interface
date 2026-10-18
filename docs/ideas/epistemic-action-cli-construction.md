# Epistemic-action CLI construction repair

- **Status:** Construction checks pass; formal experiment remains on hold in the dated issue record.
- **Source:** [Issue #8635](https://github.com/Unjuno/agent-interface/issues/8635), successor to #8629; merged construction packet [PR #8639](https://github.com/Unjuno/agent-interface/pull/8639).
- **Idea:** Repair and independently test the candidate and raw-only auditor command-line integration after the prior candidate failed before producing output.
- **Outcome:** The prior formal allocation is preserved as `HOLD_CANDIDATE_ENTRYPOINT_NAMEERROR`; it emitted no scientific rows and must not be rerun. The successor packet's 22 construction tests pass under normal and optimized CPython 3.12.10, including candidate/auditor CLI integration and a launch-failure receipt test. Candidate/auditor formal counts remain 0/0; the issue's 2026-10-08 update records a shared WSLc ownership/readiness HOLD.
- **Boundary:** Construction checks do not constitute a formal result. The dated WSLc state is specific to this allocation and is not a global stop or a grant to substitute host/Docker execution. Recheck current ownership before any future allocation.
