# Issue #5881 T0b — unchanged-target effect-option race

This is a model-free synthetic successor to the original Issue #5881 method result, testing the latest comment's distinct timing case: the primary target and its geometry remain unchanged while the optional bundled effect changes after the descriptor is formed.

Start with [RESULT.md](RESULT.md), [PLAN.md](PLAN.md), and [FREEZE.json](FREEZE.json). Candidate-visible data is `cases.json`; scorer-only outcomes are isolated in `oracle.json`. `results/decisions.jsonl`, `results/effect_events.jsonl`, and `results/audit.json` retain the run, with the exact command record in `FORMAL_LOG.md` and `RUN.json`.

Reproduce from this directory:

```powershell
python candidate.py
python effect_simulator.py
python -m unittest -v test_contract.py
python audit.py
```

No container was used: Docker Desktop's service and WSL distro were stopped and Ubuntu had no Engine socket. The experiment uses only eight deterministic synthetic cases; no model, GUI, site, user data, or network was used.

