# Run record

Freeze: `FREEZE.json`, current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

Host: Windows 10 build 26300, CPython 3.11.9. Runtime: host Python, no WSLc/container/game/model/input.

Commands:

```powershell
python .\run.py > .\results\normal.stdout.txt
python -O .\run.py > .\results\optimized.stdout.txt
python .\audit.py
```

Results: normal 8/8; optimized 8/8; independent audit 34/34. `results/raw.json` retains both cases. First scratch attempt used a Windows launcher branch's full controller blob; the relevant guard functions were unchanged, but that was not exact-main provenance. It was excluded. The retained package was rebuilt from the exact current-main Git blobs and rerun.

A02 follow-up: `python .\cover_fire_probe.py > .\results\cover_fire_probe.stdout.txt`; the independent audit consumes that output and verifies schema, compiler, and pending-loop composition.
