# Local construction validation — 2026-09-27

Scope: benchmark-engine mechanics and local overhead only. This is **not** Agent Interface, rich-model, token, or general computer-control performance evidence.

Environment: current ChatGPT Linux execution container, Python 3.13.5, Tk 8.6, X11 via Xvfb for GUI rendering checks.

## Construction checks

- `python3 -m unittest -v test_engine.py`: **14/14 PASS**.
- Python compile: `engine.py`, `arena.py`, `test_engine.py`, and `gui_smoke.py` compile successfully.
- deterministic generation: identical seed/profile/suite produces byte-identical canonical episode JSON.
- full-suite coverage: exactly 9 declared primitives per episode.
- public-state leak check: controller-facing state omits seed, public fingerprint, and hidden oracle IDs/coordinates.
- difficulty monotonicity checks pass for representative visual/motor/temporal/sequence axes.
- per-axis override check: changing `target_speed` leaves all other `DifficultyProfile` fields byte-equivalent; invalid similarity/tolerance/count/displacement overrides fail closed.
- full hidden-oracle reachability: **3 difficulty levels × 20 seeds = 60/60 full nine-stage episodes PASS** in unit tests.
- fail-closed controls exercised for premature WAIT action, stale prepared target, missing keyboard+pointer chord, drag miss, and trace deviation.
- controlled recovery requires an interruption event followed by reacquisition and a second correct action.
- stage-generation binding test confirms a physical mouse release cannot leak from a completed stage into the next stage.
- Xvfb render smoke: all **9/9 primitive renderers** produced nonempty Tk canvas output.

## Lightweight mechanics throughput

Separate local diagnostic loop:

- 1,000 full-suite episodes;
- difficulty levels cycled across `0.0, 0.25, 0.5, 0.75, 1.0`;
- total wall time: **0.939099 s**;
- throughput: **1,064.85 episodes/s**;
- mean generation: **0.2659 ms/episode**;
- mean hidden-oracle mechanics solve: **0.4144 ms/episode**;
- max observed hidden-oracle solve in this loop: **1.1251 ms**;
- process `ru_maxrss`: **93,992 KiB**.

These measurements include Python/container overhead and are not portable benchmark claims. They establish only that the mechanics are cheap enough for rapid local iteration in this environment.

## Container note

A Dockerfile is provided for a minimal Python/Tk/Xvfb image, but this execution environment does not contain Docker or Podman. Therefore **no container image build/run claim is made here**.

## Promotion gates still open

1. Freeze the controller-visible observation/input contract and independent scorer semantics.
2. Run a genuine paired Plain-rich-model baseline and one Agent Interface candidate on identical fresh episodes with isolated model sessions.
3. Sweep individual difficulty axes and selected interactions; report correctness-preserving failure frontiers.
4. Use a hardened evaluator boundary that prevents controller access to seed/source/process/private scorer state.
5. Add held-out composition/generator families generated after candidate freeze where feasible.
6. Add external model/image/token/cache/resource accounting in the paired harness.
7. Replicate retained mechanisms on independent real-app/domain tasks before any general capability claim.
