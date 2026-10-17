# Visual-context-staleness A01 package

A current-main boundary replay using an exact adjacent retained V39 frame pair and its typed signal rows.

- [Hypothesis and decision rule](HYPOTHESIS.md)
- [Result and limits](REPORT.md)
- [Freeze / Git blob identities](FREEZE.json)
- [Exact input event log and frames](inputs/)
- [Decoded pixel/frame digest audit](inputs/frame-audit.json)
- [Raw WSLc transcript](results/wslc.stdout.txt)
- [Structured outcome](results/result.json)
- [As-run source/result auditor](audit_visual_context.py; retained unchanged)
- [Post-run byte-bound auditor](audit_visual_context_v2.py), which decodes the PNGs and reconciles the captured WSLc records with `result.json`
- [Post-run immutable reproduction check](test_visual_context_staleness_v2.py), which writes runtime prompts to a temporary directory
- [SHA-256 manifest](SHA256SUMS)

Original one-shot procedure (already consumed): build `visual-context-staleness:a01-20261012` under WSLc 3.0.1.0 from this directory and run once with `--network none --cpus 1 --memory 512m`. The retained transcript and exit receipt below are the result; do not rerun this allocation. No cgroup enforcement is inferred from requested flags.

The single frozen WSLc execution is complete and retained; its original test, freeze, container, transcript and outputs remain unchanged. A post-run local check may run `python -m unittest -v test_visual_context_staleness_v2` and `python audit_visual_context_v2.py`; this does not rerun the WSLc allocation. The v2 test avoids mutating the tracked frozen prompt.

This is a fake-planner construction replay, not a live threat-control result.
