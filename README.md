# Agent Interface

**A faster interface between AI agents and computers.**

> **Status: Research Preview.** Agent Interface is an active systems research project, not a production automation framework. This repository is the public research record: experiments, benchmark harnesses, design notes, and the code that is shaping the eventual runtime.

[Landing page](https://unjuno.github.io/agent-interface/) · [Research index](RESEARCH.md) · [Architecture](docs/architecture.md) · [Open an idea](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml) · [Issues](https://github.com/Unjuno/agent-interface/issues)

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

The goal is not to make the model smarter. The goal is to remove work that carries little or no new information: repeated model boundaries, redundant screenshots, repeated serialization, predictable failed routes, and deterministic control mechanics that can be handled locally.

## Design ideas shaping the system

These are the main ideas currently being implemented or tested. The important question for each one is: **what information or work can be removed without removing information the agent actually needs?**

| Idea | First-principles reason | Expected effect | State |
|---|---|---|---|
| **Universal fallback** | An optimization must never be required for basic correctness | Unknown apps still work; learned routes can safely fail | Current baseline |
| **Self-compiling semantic methods** | Repeated successful traces should not be serialized and planned from scratch forever | Fewer model turns and fewer planner bytes | Current baseline |
| **Separate semantic, binding, route, and observation-cache lifetimes** | A stale coordinate or window instance does not imply the task meaning became invalid | Less relearning and fewer unnecessary fallbacks | Promoted in real-app experiments |
| **Guarded Hierarchical Deoptimization (GHD)** | If a cheap observable guard can prove a fast route is stale, executing it and waiting for failure is wasted work | Better reliability and much lower failure tails | Promoted in real-app experiments |
| **Latest-only visual state** | Old frames are not additional evidence about the current GUI state | Less stale-state processing; higher control precision | Runtime principle |
| **Event-driven observation** | Polling when nothing changed creates work but no information | Fewer captures and lower observation overhead | Used in X11 experiments |
| **Observation gating** | An unchanged or task-irrelevant screen should not consume another model-visible image | Lower image/token cost without intentionally discarding relevant state | Active research track |
| **Changed-region / visual-delta feedback** | When only a small region changed, the full frame is redundant | Lower visual bandwidth; potentially cleaner feedback | Active research track |
| **Local verification before model escalation** | Deterministic postconditions do not always require model interpretation | Fewer model calls/images while preserving an uncertainty fallback | Active design direction |
| **Input delivery semantics** | Sending an OS event is not the same as the application consuming it | Higher correctness for text, chords, drag, modal transitions | Measured on real X11 apps |
| **Closed-loop local motor control** | Pointer movement and on-screen movement are not always identical | Higher fine-control precision without adding a local neural model | Experimental baseline |

The table is intentionally not a feature checklist. Some entries are promoted baselines; others are active hypotheses that still need stronger evidence.

## Have a better idea?

This project is deliberately open to design ideas, not only bug reports.

If you see a way to make computer use **more token-efficient, more accurate, more reliable, simpler, or more general**, open an [**Idea issue**](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml). You do **not** need a finished implementation or benchmark.

Useful proposals usually answer three simple questions:

1. **What is the system wasting or getting wrong?** — image observations, model calls, serialization, retries, stale state, fragile assumptions, etc.
2. **What should change?** — the smallest mechanism that removes that waste or error.
3. **Why should quality be preserved or improved?** — what information remains available, and what failure mode still has a fallback?

If the idea is mature enough to benchmark, use the stricter [**Research proposal**](https://github.com/Unjuno/agent-interface/issues/new?template=research-proposal.yml) form. That form turns the idea into a falsifiable H/T/D/C/U experiment.

Particularly useful idea areas right now:

- suppressing unchanged or irrelevant visual observations;
- visual state deltas and cacheable frame state;
- deciding when a guard is cheaper than failure-and-recovery;
- discovering reusable methods without privileged app APIs;
- reducing planner serialization without hiding semantics;
- local verification that avoids unnecessary model escalation;
- robust input-delivery barriers across GUI toolkits;
- cross-platform abstractions beyond X11;
- adversarial benchmarks that expose hidden correctness failures.

## Current research direction

The current design has four core architectural ideas:

1. **Universal control** — unknown apps must work from keyboard, pointer, focus, scroll, drag, text, and observation primitives.
2. **Self-compiling methods** — successful traces can become reusable semantic methods and short workflows.
3. **Guarded hierarchical deoptimization** — binding, focus/preconditions, optimized routes, observation caches, and semantic methods have different lifetimes. A stale route should not destroy valid semantic knowledge.
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
| Layered binding + route guards | 72/72 success with predictable stale-route execution eliminated before execution | Chromium geometry drift + real process replacement |

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
├── README.md               # product/research entry point + design ideas
├── RESEARCH.md             # evidence ledger and experiment index
├── ROADMAP.md              # current research sequence
├── docs/                   # architecture and product notes
├── research/
│   ├── real_apps_v1/       # fixed-wait vs sparse/reactive control
│   ├── real_apps_v2/       # route suspend / method lifetime experiments
│   └── real_apps_v3/       # guarded hierarchical deoptimization
├── site/                   # GitHub Pages landing page
└── .github/ISSUE_TEMPLATE/ # idea, research proposal, and bug forms
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

## Repository vs Releases

The **repository is research-first**: experiments, rejected ideas, reports, raw summaries, and evolving implementation work live here.

**GitHub Releases are intended to become user-facing runnable distributions** — something a user can download, install or unpack, and actually try. A runnable preview should include the executable/package, checksum, and a minimal quickstart.

The existing `v0.0.1-research.*` prereleases are archival research snapshots created while bootstrapping the repository. They should not be interpreted as finished user distributions. Future user-facing previews will use a separate release track once the runnable surface is coherent enough to support.

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
