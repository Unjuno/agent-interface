# Commands and captured process outcomes

Frozen CPU-only suite (before probe):

```sh
python -m unittest -v test_probe
python -m py_compile probe.py audit.py test_probe.py
```

Observed: `Ran 4 tests ... OK`; syntax compilation exit 0.

Single construction probe (invoked once, after Issue #5243 freeze comment):

```sh
python -B research/x11/issue5243-private-xvfb-construction-20260929/probe.py \
  research/x11/issue5243-private-xvfb-construction-20260929/results/construction-01
```

The Windows launcher was `wsl -d archlinux -- bash -lc` with `cd` to the
worktree followed by the command above. Observed wrapper exit code: 2. No retry.

Frozen raw audit (invoked once on the retained record):

```sh
python -B audit.py results/construction-01/result.json
```

Observed audit exit code: 1; stderr is retained verbatim as
`results/construction-01/audit.stderr`. No retry.
