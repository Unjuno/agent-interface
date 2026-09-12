# Agent Interface

**A faster interface between AI agents and computers.**

> **Status: Research Preview.** Agent Interface is an active systems research project, not a production automation framework. The current repository publishes the experiments, benchmark harnesses, design notes, and research snapshots that are shaping the runtime.

[Landing page](https://unjuno.github.io/agent-interface/) · [Research index](RESEARCH.md) · [Architecture](docs/architecture.md) · [Releases](https://github.com/Unjuno/agent-interface/releases)

## Why this exists

Most computer-use loops repeatedly pay for the same boundary:

```text
model -> one action -> screenshot -> model -> one action -> screenshot -> ...
```

Agent Interface explores a different systems boundary:

```text
strong planner
    -> semantic method / short reactive program
    -> guarded local execution
    -> observe only meaningful change
    -> deoptimize only the stale layer
    -> return to the model when semantics require it
```

The goal is not to make the model smarter. The goal is to stop wasting model turns, image observations, serialization, and recovery work on deterministic control mechanics.

## Current research direction

The current design has four core ideas:

1. **Universal control** — unknown apps must work from keyboard, pointer, focus, scroll, drag, text, and observation primitives.
2. **Self-compiling methods** — successful traces can become reusable semantic methods and short workflows.
3. **Guarded hierarchical deoptimization (GHD)** — binding, focus/preconditions, optimized routes, observation caches, and semantic methods have different lifetimes. A stale route should not destroy valid semantic knowledge.
4. **Observation gating** — if the screen has not meaningfully changed, do not send another image. If only a relevant region changed, escalate only that region.

See [docs/architecture.md](docs/architecture.md).

## What has been measured so far

These are research measurements, not production claims.

| Experiment | Result | Scope |
|---|---:|---|
| Real-app sparse reactive control | B1 reached 8/8 success on XTerm, Chromium, Calc, and Inkscape in the development screen | Linux/X11, small `n=8/app` |
| Route-level deoptimization | Inkscape observation reduced **51.9%** and planner-byte proxy **27.8%** vs method invalidation | 72 hidden episodes, real Inkscape |
| Pre-execution guards | XTerm p99 reduced about **77.5%** | 72 hidden episodes, focus drift |
| Pre-execution guards | Chromium p99 reduced about **75.4%** | 72 hidden episodes, geometry drift |
| Layered binding + route guards | 72/72 success with route failure eliminated before execution | Chromium geometry drift + real process replacement |

Raw reports and CSVs are in [`research/`](research/). The benchmark policy treats correctness as a hard gate and keeps proxy bytes, observed pixels, local timing, and model/token claims separate.

## What is **not** proven yet

- No general cross-platform result: current real-app work is Linux/X11.
- No production-grade automatic method discovery is claimed yet.
- No end-to-end LLM latency or real image-token reduction has been measured yet.
- Synthetic results are not substituted for real-app evidence.
- Current Python code is an experimentation vehicle. A systems implementation language is a later stabilization step, after semantics stop moving quickly.

## Repository layout

```text
.
├── README.md               # product/research entry point
├── RESEARCH.md             # evidence ledger and experiment index
├── ROADMAP.md              # current research sequence
├── docs/                   # architecture, protocol notes, safety, launch notes
├── research/
│   ├── real_apps_v1/       # fixed-wait vs sparse/reactive control
│   ├── real_apps_v2/       # route suspend / method lifetime experiments
│   └── real_apps_v3/       # guarded hierarchical deoptimization
├── site/                   # GitHub Pages landing page
└── .github/workflows/      # Pages + GitHub research releases
```

## Reproducing the research

The real-app harnesses expect a Linux/X11 environment with the tested desktop applications installed. Current Python dependencies:

```bash
python -m pip install -r requirements-research.txt
```

Example:

```bash
python research/real_apps_v1/real_app_suite_v1.py --help
python research/real_apps_v3/multiapp_lifecycle_bench.py --help
```

The scripts can inject real GUI input. Run them only in an isolated X session/container you are willing to control programmatically.

## Release policy

GitHub Releases are immutable research checkpoints, not declarations of production stability.

- `v0.x.y-research.N` — reproducible research snapshot; expected to change.
- future `v0.x` previews — only after a coherent runnable runtime surface exists.
- stable releases — only after semantics, correctness gates, cross-app tests, and implementation boundaries are substantially frozen.

The first release intentionally packages reports, CSVs, harnesses, and design notes together so claims can be audited against the experiment that produced them.

## Research discipline

Every promoted change should answer:

- **H** — falsifiable hypothesis
- **T** — minimum test and environment
- **D** — PASS / FAIL / UNCERTAIN criterion
- **C** — competing explanation / failure mode
- **U** — uncertainty and dominant error source

Correctness is a hard gate. Tiny noisy wins are not promotions. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).
