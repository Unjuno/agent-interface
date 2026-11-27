# A14 package

A one-run WSLc construction experiment of the current-main pending-planner / fresh-action-admission boundary.

- [Hypothesis and decision gates](HYPOTHESIS.md)
- [Run report and scope](REPORT.md)
- [Freeze and source identities](FREEZE.json)
- [Raw WSLc transcript](results/wslc.stdout.txt)
- [Structured results](results/result.json)
- [Independent audit](audit_a14.py)
- [Preserved preflight failures](FAILED_PREFLIGHT_01.md)
- [SHA-256 manifest](SHA256SUMS)

Reproduce the final run with WSLc 3.0.1.0: `wslc build -t a14-pending-ammo-staleness:20261012 .` then `wslc run --rm --network none --cpus 1 --memory 512m a14-pending-ammo-staleness:20261012`. The WSLc test was run once. Do not infer cgroup/swap enforcement from requested flags; runtime warned memory was limited without swap.

Disposition is construction-only. The fake client, synthetic answer and typed observations do not test a model, game, OS input, physical release, task effect, recovery, or MAP01 outcome.
