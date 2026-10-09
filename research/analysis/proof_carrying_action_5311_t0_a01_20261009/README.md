# Issue #5311 T0 A01

Finite, standard-library-only test of a producer-supplied certificate for bounded action admission. The certificate binds a canonical plan digest, but the checker also revalidates each action against the certificate and policy because the schema contains no proof rule that can soundly compress those checks. The preregistered comparison therefore includes all costs of that admission path. Result: `FAIL_COST_GATE_SCOPED` (80 inspections for full reconstruction, 136 for certificate admission on eight valid plans).

Read [protocol](PROTOCOL.md), [freeze](FREEZE.json), [report](REPORT.md), and [run record](RUN_RECORD.md) before interpreting the retained [candidate output](results/candidate.json) and [independent audit](results/audit.json). This is synthetic method evidence only. No GUI, model, network, GPU, participant, application effect, safety guarantee, production performance, or product claim is made.
