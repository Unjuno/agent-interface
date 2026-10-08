# Issue #8629 T0 A01 — independent held-out diagnostic screen

Successor study to Issue #8623; it preserves A01's synthetic method result and does not reinterpret it. This experiment uses four fixed seeds, six authored evidence strata, five deterministic policy implementations, and three arms (720 policy-arm-case rows). Candidate inputs are separated from oracle labels, and the auditor is a separate raw-only implementation.

This is still a finite synthetic method screen. Seed changes bind case IDs and provenance receipts over the same six semantic strata; it does not establish broad generalization or real-agent competence.

The source-first protocol is in [PLAN.md](PLAN.md), and all construction red/green evidence and remaining boundaries are in [CONSTRUCTION.md](CONSTRUCTION.md). Candidate/auditor formal execution has not yet occurred. The frozen inputs, one-shot receipts, and final scoped interpretation will be retained alongside this README.
