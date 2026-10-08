# V39 stale-rejection continuation regression A02

## H / T / D / C / U

- **H:** A stale preacceptance rejection must skip ordinary iteration completion and continue the outer loop.
- **T:** Parse the V39 controller at the tested PR head and assert the outer `if stale_rejection is not None` branch ends in `continue`. Remove that exact statement in a temporary copy as the negative mutation.
- **D:** PASS when positive runs succeed in normal and optimized Python, and both mutated-source runs fail at the targeted assertion.
- **C:** This establishes one AST control-flow edge only; it does not execute the controller loop.
- **U:** Fresh observation/planner behavior, live game/GUI recognition, OS input and release, recovery benefit, task effect, and MAP01 completion are untested.

The dependency-free regression lives at `research/doom/test_map01_v39_stale_rejection_continue_static.py`. `FREEZE.json` binds the tested PR source and test blob. Four raw runs are retained under `results/`.

Reproduce from the repository root:

```sh
python3 -m unittest research.doom.test_map01_v39_stale_rejection_continue_static -v
python3 -O -m unittest research.doom.test_map01_v39_stale_rejection_continue_static -v
python3 research/doom/v39_stale_rejection_continue_a02_20261009/verify.py
```
