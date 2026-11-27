# A16 package

A paired threshold experiment of current-main pending-turn behavior.

- [Hypothesis and decision gates](HYPOTHESIS.md)
- [Run report](REPORT.md)
- [Freeze and source identities](FREEZE.json)
- [Raw WSLc output](results/wslc.stdout.txt)
- [Structured cases](results/result.json)
- [Independent audit](audit_a16.py)
- [SHA-256 manifest](SHA256SUMS)

The WSLc candidate is run exactly once. Reproduce with WSLc 3.0.1.0 using `wslc build -t a16-pending-ammo-threshold:20261012 .` then `wslc run --rm --network none --cpus 1 --memory 512m a16-pending-ammo-threshold:20261012`. No cgroup/swap enforcement is claimed from requested flags.

Construction-only; no model, live game, actual executor, or physical input is used.
