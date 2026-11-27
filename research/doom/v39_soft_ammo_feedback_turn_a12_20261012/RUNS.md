# A12 run record

The local final-source preflight (`python -m unittest -v test_a12_soft_feedback_turn.py`, CPython 3.11.9) passed 2/2. The frozen WSLc test command ran once:

```text
wslc run --rm --network none --cpus 1 --memory 512m a12-soft-ammo-feedback:20261012
```

It passed 2/2 under CPython 3.14.8 and exited 0. Raw output is `results/wslc.stdout.txt`; the structured feedback receipt is parsed from its `A12_RESULT` line. `results/environment*.txt` records image/runtime and the separate cgroup-only probe. `FREEZE.json` and `source_hashes.json` bind the exact source, test, image base, and requested constraints. `audit_a12.py` does not execute tests.
