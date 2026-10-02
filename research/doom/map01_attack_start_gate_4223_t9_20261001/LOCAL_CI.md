# Local validation

Run structural contract tests and workspace checks without a game candidate:

```sh
python3 -m unittest discover -s research/doom/map01_attack_start_gate_4223_t9_20261001 -v
python3 -m py_compile research/doom/map01_attack_start_gate_4223_t9_20261001/*.py
git diff --check
python3 research/check_workspace_index.py --git-tree
```

These checks are not experimental evidence. The formal candidate is run
separately exactly once through the `orchestrate.py` path in `PLAN.md`; its
source/image identities, logs, raw receipt and independent audit are retained
in `REPORT.md`.
