# Local container validation — 2026-09-27

Scope: mechanics and benchmark-overhead validation only. This does **not** measure an Agent Interface candidate, rich-model quality, token efficiency, or general computer-control performance.

Environment: current ChatGPT execution container, Python 3.13.5, Linux X11 via Xvfb for GUI smoke.

## Checks

- `python3 -m unittest -v test_engine.py`: **8/8 PASS**.
- deterministic generation: identical seed+difficulty produced byte-identical canonical episode JSON.
- public-state leak check: seed and hidden target object IDs were absent from controller-facing public state.
- declared difficulty monotonicity: target radius/deadlines decreased while target speed/distractors/typing length increased from difficulty 0.0 to 1.0.
- positive-control sweep: **5 difficulty levels x 200 seeds = 1,000/1,000 PASS** using the hidden-oracle test solver. This validates generator/scorer reachability only.
- fail-closed controls: premature click during WAIT produced `premature_action`; clicking the prepared target after SWITCH produced `stale_action`.
- GUI smoke: Tk arena launched under Xvfb/Openbox and remained live for the bounded 3 s smoke interval without an attached controller.
- Python compile check: `engine.py`, `arena.py`, and `test_engine.py` compiled successfully.

## Lightweight mechanics throughput

A separate 1,000-episode generation + hidden-oracle mechanics loop at difficulty 0.5 completed in:

- total wall time: **0.630429 s**;
- throughput: **1,586.22 episodes/s**;
- mean episode generation: **0.1342 ms**;
- mean hidden-oracle mechanics solve: **0.3536 ms**.

`ru_maxrss` for the whole Python process was 93,352 KiB in this container; that number includes interpreter/container instrumentation and is not attributed to the arena alone.

These numbers are local diagnostic evidence, not a portable benchmark claim. Formal performance work should rerun them on the declared evaluation host and report host/runtime conditions.

## Remaining validation before benchmark promotion

1. pair one plain rich-model computer-control baseline and one Agent Interface candidate on identical fresh episode seeds;
2. freeze controller-visible observations/input primitives and independent scorer semantics;
3. sweep individual difficulty axes and verify interpretable failure-frontier movement rather than only aggregate difficulty;
4. add an evaluator/container boundary that prevents controller access to source, process args, seed, hidden state, and scorer internals;
5. add fresh/held-out composition families so public generator code does not become the benchmark-specific optimization target;
6. retain this arena as a screening/regression fixture unless cross-domain transfer is independently established under Issue #12-style held-out evaluation.
