# Visual-context-staleness A01 package

A current-main boundary replay using an exact adjacent retained V39 frame pair and its typed signal rows.

- [Hypothesis and decision rule](HYPOTHESIS.md)
- [Result and limits](REPORT.md)
- [Freeze / Git blob identities](FREEZE.json)
- [Exact input event log and frames](inputs/)
- [Decoded pixel/frame digest audit](inputs/frame-audit.json)
- [Raw WSLc transcript](results/wslc.stdout.txt)
- [Structured outcome](results/result.json)
- [Independent source/result auditor](audit_visual_context.py)
- [SHA-256 manifest](SHA256SUMS)

Reproduce under WSLc 3.0.1.0 by building `visual-context-staleness:a01-20261012` from this directory and running once with `--network none --cpus 1 --memory 512m`. No cgroup enforcement is inferred from requested flags.

This is a fake-planner construction replay, not a live threat-control result.
