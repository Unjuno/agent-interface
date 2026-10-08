# Negative-query counterfactual responsibility — Issue #8624 T0 A01

This package tests the finite method proposal in [Issue #8624](https://github.com/Unjuno/agent-interface/issues/8624). It compares positive minimal supports and nearest outcome flips with signed-fact actual causes derived from compatible prime implicants, against a separate exhaustive intervention auditor.

The frozen model has seven cases and 2,120 total Boolean assignments. It includes a monotone control, two negative-query examples, paired systems with identical positive support and minimal flip summaries but different causes, a robustness-radius-one case with a designated minimum contingency of three, and an eleven-fact parity case whose prime enumeration is explicitly refused at the frozen cube-scan budget.

The A01 first outcome is STOP_CANDIDATE_EXIT_AFTER_OUTPUT: the candidate wrote a complete-looking JSON payload, then exited 1 because its CLI wrapper referenced an undefined local variable. The independent auditor was correctly not started. The output is preserved as failure evidence and must not be promoted to PASS or rerun under A01. Details are in [REPORT.md](REPORT.md), [FREEZE.json](FREEZE.json), and [RUN_RECORD.json](RUN_RECORD.json). Construction controls are in test_construction.py.

Scope is limited to authored finite rule systems and their declared mutable facts. This does not test screenshot completeness, query freshness, visual perception, real GUI causation, live action authority, production incidence, or user/product benefit.
