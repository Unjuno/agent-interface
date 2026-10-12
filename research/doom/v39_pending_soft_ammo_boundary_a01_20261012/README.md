# A01 replay package

The source snapshots are byte-identical to the named `origin/main` blobs in `FREEZE.json`. The runner executes the actual paired HUD monitor functions and statically checks the exact pending-turn loop; it does not launch Doom, a model, or OS input.

Run from this directory on Python 3.11+:

```powershell
python .\run.py > .\results\normal.stdout.txt
python -O .\run.py > .\results\optimized.stdout.txt
python .\audit.py
```

Expected: each mode reports 8/8 runner predicates; the independent audit reports 17/17. The boundary is synthetic. It does not establish whether a running cover contains fire, whether continuing fire below an action minimum is harmful, or any live task effect. See `HYPOTHESIS.md` for decision limits.

