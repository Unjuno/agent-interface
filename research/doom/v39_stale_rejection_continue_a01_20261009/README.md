# V39 stale-rejection outer-loop continuation regression A01

## H / T / D / C / U

- **H:** A stale preacceptance Executor rejection must leave the candidate closed and continue the outer iteration so the next planner turn starts from fresh source.
- **T:** Parse the exact V39 `main()` from frozen current main and assert the top-level `if stale_rejection is not None` branch ends in `continue`. Delete that statement in an isolated source copy as the negative mutation.
- **D:** PASS if the test succeeds normally and under `python -O`, while both mutated-source runs fail specifically at the new assertion.
- **C:** This checks one static control-flow edge; it does not execute the controller loop or establish timing or runtime behavior.
- **U:** Live planner interruption, GUI/game recognition, OS/physical release, recovery benefit, useful task effect, and MAP01 completion remain untested.

## Results

The frozen controller contains the required branch continuation. Removing its direct `continue` makes the new test fail with the expected assertion in both interpreter modes. Raw stdout, stderr, and exit codes are in `results/`.

Reproduce the positive test from repository root with `PYTHONPATH=research/doom:research/live_control`:

```sh
python3 -m unittest test_map01_v39_stale_rejection_continue -v
python3 -O -m unittest test_map01_v39_stale_rejection_continue -v
```

`FREEZE.json` pins all imported repository Python sources, the source commit, PR head, interpreter, platform, and exact mutation. `verify.py` independently checks those identities, all four retained outcomes, and the package manifest.
