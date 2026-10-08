# Guard-induced proposal risk T0

Finite exact simulator for Issue [#6143](https://github.com/Unjuno/agent-interface/issues/6143). It separates (a) guard confusion-table performance under a fixed proposal distribution from (b) all-launched harm, unfinished work, refusals, retries, and abstract proposal-work units when the proposal distribution changes.

`PLAN.md` is the protocol and H/T/D/C/U. `fixture.json` freezes exact rational inputs. `simulator.py` is the candidate recursion; `audit.py` independently replays the input iteratively without importing candidate code. `runs/formal-01/` retains the single candidate and audit outputs. This is a finite synthetic method check only; it is not an empirical Agent Interface result.

Reproduce construction checks:

```sh
python3 -m unittest discover -s . -p 'test_*.py' -v
python3 -m py_compile simulator.py runner.py audit.py test_simulator.py test_audit.py
```

Formal container commands and limits are recorded in `FREEZE.json` and `RUN.json`. Outputs use exact rational strings; no random seed or retry exists.
