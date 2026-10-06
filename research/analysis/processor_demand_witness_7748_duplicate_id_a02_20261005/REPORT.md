# Issue #7748 duplicate-job-ID boundary A02 report

**Result: `PASS_DUPLICATE_ID_BOUNDARY_SCOPED`.** The candidate and raw-only auditor each ran exactly once and exited 0. The auditor reconstructed all three frozen rows with no errors; the duplicate-ID case held as `HOLD_DUPLICATE_JOB_ID`, while the two distinct-ID fixtures remained eligible with their expected feasibility classifications. Formal retries: zero.

A01 remains a separate `STOP_AUDITOR_EXIT_MISMATCH`: its auditor wrote a zero-error scoped PASS JSON but returned exit 1 because its CLI still compared against the predecessor class-boundary status. A02 was preregistered as a fresh allocation. Its new CLI contract test first failed against the inherited mapping, then passed after the narrow success-status correction. A01 evidence was not changed, rerun, or pooled.

This PASS covers only the finite duplicate/malformed job-identity input boundary and the three authored integer-tick traces. It does not establish general schedulability, full CBS, real operating-system or scheduler timing, Agent Interface runtime/resource behavior, GUI/model behavior, safety, task effects, or physical release. Candidate and auditor have separate implementations but were authored by one researcher; independent human review remains outstanding.

Docker/OrbStack's read-only image listing failed before candidate launch on a containerd content blob with `operation not supported`. The preregistered host-only CPython 3.14.5 fallback was used for this standard-library model. No container isolation or resource-enforcement result is claimed.

A supplemental post-run call-level probe rejected three mutations: duplicate marked eligible, job identity changed after candidate output, and a row omitted. The probe is separately labeled in `results/POST_RUN_MUTATION_CONTROLS.json`; it did not invoke either formal CLI or change the one-candidate/one-auditor budget.

See [protocol](PROTOCOL.md), [frozen sources and inputs](FREEZE.json), [formal receipts](RUN.json), [construction record](CONSTRUCTION.log), and preserved raw/audit output under `results/`.
