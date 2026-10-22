# A10 run record

Local preflight command: `python -m unittest -v test_a10_cancel_composition.py` (CPython 3.11.9), one final frozen-source run. It passed 1/1.

WSLc command:

```text
wslc run --rm --network none --cpus 1 --memory 512m a10-authored-pair-cancel:20261012
```

The WSLc test ran once under CPython 3.14.8 and exited 0. Its full captured output is `results/wslc.stdout.txt`; `results/result.json` is parsed from its machine-readable line, not from a second test run. `results/environment.txt` contains the image/runtime identity; `results/environment-probe.txt` contains a separate cgroup-only probe. The exact source identities, Python base manifest, test digest, and Containerfile digest are in `FREEZE.json`.

`audit_a10.py` is non-executing: it rechecks IDs, hashes, the retained transcript and structured receipt. The initial authoring smoke ran before a print-only output change; it is not included as a frozen test result. No `-O` run was made.
