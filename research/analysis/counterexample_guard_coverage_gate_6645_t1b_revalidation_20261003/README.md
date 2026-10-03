# Issue #6645 T1b independent integration revalidation

Two separate dispositions: the retained T1b evidence is independently reconstructed on the Windows host; the new WSLc neutral-ID candidate probe remains on HOLD and has not run. The parent T1b allocation and its 30 files are unchanged.

- [Protocol and H/T/D/C/U](PREREGISTRATION.md)
- [Scoped roadmap and integration handoff](ROADMAP.md)
- [Result and limits](REPORT.md), [run record](RUN_RECORD.md), [WSLc STOP](STOP.md)
- [Frozen source identities](AUDIT_FREEZE.json), [package checksums](SHA256SUMS)
- Read-only [auditor](independent_audit.py) and [pure verifier controls](test_independent_audit.py)
- [Construction history](CONSTRUCTION.md), including the retained failed verifier run
- [Two environment-only WSLc preflights](results/PREFLIGHT.md)
- [Prepared candidate-only payload](pending_label_probe/PROPOSAL.json); a proposal, not launch authority
- [Immutable parent T1b package](../counterexample_guard_coverage_gate_6645_t1b_v1/)

## Reproduce the read-only checks

From the repository root, without Docker Desktop or WSLc:

```powershell
python -B -m unittest discover -s research/analysis/counterexample_guard_coverage_gate_6645_t1b_revalidation_20261003 -p test_independent_audit.py -v
python -B research/analysis/counterexample_guard_coverage_gate_6645_t1b_revalidation_20261003/independent_audit.py --package research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1
```

Neither command imports or executes the parent candidate. Tests of the pending label-output checker use an explicitly synthetic copy of retained output, not a new candidate result. The three proposal inputs contain no oracle, retained raw, report, or repository mount.

The selected Windows container route is WSLc 3.0.1.0 without Docker Desktop. No new WSLc invocation follows recognition of the #5085 shared-state HOLD. This package demonstrates neither runtime speedup nor memory-limit enforcement; the host audit is resource-independent evidence preservation.
