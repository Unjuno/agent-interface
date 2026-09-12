# Agent Interface

**A faster interface between AI agents and computers.**

> **Research thesis:** AI agents are becoming highly capable, but the computer-control tools they use are still primitive. If the model is held fixed, a better interface should let the same agent use computers with less waiting, fewer redundant observations, fewer model boundaries, and less recovery work at the same correctness.

> **Status: Research Preview.** This repository is the public research record. User-facing GitHub Releases will be reserved for runnable distributions that people can actually download and try.

[Landing page](https://unjuno.github.io/agent-interface/) · [Principles](docs/principles.md) · [Research index](RESEARCH.md) · [Architecture](docs/architecture.md) · [Roadmap](ROADMAP.md) · [Open an idea](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml)

## The hypothesis

Most computer-use systems still resemble:

```text
model -> one action -> screenshot -> model -> one action -> screenshot -> ...
```

Agent Interface asks whether the interface, not only the model, is now a major bottleneck:

```text
strong planner
    -> semantic method / short reactive program
    -> guarded local execution
    -> immediate useful feedback
    -> observe only meaningful change
    -> deoptimize only the stale layer
    -> return to the model when semantics require it
```

The clean experiment is simple:

```text
same model
same task
same environment
same correctness requirement

only the interface changes
```

Then measure model boundaries, serialization, observation cost, latency, retries, recovery, and eventually real token use separately.

## Component principles

The eventual tool should satisfy four constraints from the start:

1. **Install quickly.** A user should be able to install or unpack it, start it, connect an agent, and use it without app-specific setup.
2. **Work with every agent.** The core should be model- and vendor-agnostic. Model-specific adapters belong outside the runtime core.
3. **Do not stop the agent's thinking.** After an action, return the earliest trustworthy feedback instead of blocking on fixed waits or unnecessarily complete observations. Reduce **agent idle time**.
4. **React locally.** Input delivery, state-change detection, local verification, retry, and fine motor correction should stay in the local fast path when they do not require semantic reasoning.

Full rationale: [`docs/principles.md`](docs/principles.md).

## Ideas shaping the system

| Idea | Why it exists | Expected effect | State |
|---|---|---|---|
| **Universal fallback** | Optimizations must never be required for basic correctness | Unknown apps still work | Baseline |
| **Self-compiling semantic methods** | Repeated successful traces should not be replanned forever | Fewer model turns / less serialization | Baseline |
| **Layered lifetimes** | A stale coordinate, binding, or visual cache does not imply the task meaning changed | Less relearning | Promoted |
| **Guarded Hierarchical Deoptimization** | Predictably stale fast paths should be skipped before failure | Better reliability / lower tail latency | Promoted |
| **Latest-only visual state** | Old frames are not extra evidence about the current GUI | Less stale-state processing | Runtime principle |
| **Event-driven observation** | Polling without state change creates work but no information | Fewer captures / faster feedback | Experimental baseline |
| **Observation gating** | An unchanged or irrelevant screen should not consume another model-visible image | Lower visual/token cost | Active research |
| **Visual delta / changed-region feedback** | A small local change does not justify resending the whole frame | Lower visual bandwidth | Active research |
| **Local verification** | Deterministic postconditions do not always need model interpretation | Fewer model escalations | Active design |
| **Input delivery semantics** | Sending an OS event is not the same as application consumption | Higher correctness | Measured |
| **Closed-loop motor control** | Pointer movement and on-screen movement are not always identical | Better fine control | Experimental |

## Current evidence

These are scoped research measurements, not production claims.

| Experiment | Result | Scope |
|---|---:|---|
| Sparse reactive control | B1 reached 8/8 success on XTerm, Chromium, Calc, and Inkscape in the development screen | Linux/X11, small `n=8/app` |
| Route-level deoptimization | Inkscape observation reduced **51.9%** and planner-byte proxy **27.8%** vs method invalidation | 72 hidden episodes |
| XTerm focus guard | p99 reduced about **77.5%** | 72 hidden episodes |
| Chromium geometry guard | p99 reduced about **75.4%** | 72 hidden episodes |
| Layered binding + route guards | 72/72 success with predictable stale-route execution eliminated before execution | Chromium drift + process replacement |

Raw reports and CSVs are under [`research/`](research/). `planner bytes` are not tokens, `observed pixels` are not image tokens, and local wall time is not model-in-loop latency.

## Repository map

```text
.
├── README.md                  # project entry point
├── RESEARCH.md                # evidence ledger
├── ROADMAP.md                 # research sequence
├── docs/
│   ├── README.md              # documentation index
│   ├── principles.md          # thesis + component principles
│   ├── architecture.md        # current promoted architecture
│   └── product-hunt.md        # launch notes
├── research/
│   ├── requirements.txt       # research-only Python dependencies
│   ├── real_apps_v1/          # input delivery + sparse reactive control
│   ├── real_apps_v2/          # method lifetime vs route lifetime
│   └── real_apps_v3/          # guarded hierarchical deoptimization
├── runtime/
│   └── README.md              # future runnable runtime workspace
├── release/
│   └── README.md              # user-facing release contract
├── site/                      # GitHub Pages landing page
└── .github/
    ├── ISSUE_TEMPLATE/        # idea / research proposal / bug forms
    └── workflows/             # Pages + manual research archive
```

## Reproducing the research

Current real-app harnesses target Linux/X11 and can inject real keyboard and pointer input. Use an isolated X session or disposable container.

```bash
python -m pip install -r research/requirements.txt
python research/real_apps_v1/real_app_suite_v1.py --help
```

Read [`RESEARCH.md`](RESEARCH.md) before interpreting benchmark numbers.

## Ideas and contributions

This project explicitly accepts design ideas, not only bug reports.

If you can remove unnecessary observations, model calls, serialization, retries, latency, or fragile assumptions **without removing information the agent needs**, open an [Idea issue](https://github.com/Unjuno/agent-interface/issues/new?template=idea.yml).

A useful idea can be simple:

1. What work or information flow is wasteful today?
2. What is the smallest mechanism that removes it?
3. Why should correctness or precision be preserved or improved?

If it is mature enough to benchmark, use the stricter [Research proposal](https://github.com/Unjuno/agent-interface/issues/new?template=research-proposal.yml) form.

## Repository vs Releases

- **Repository:** research, experiments, rejected ideas, benchmarks, design notes, and evolving implementation work.
- **GitHub Releases:** future runnable distributions a user can download, install/unpack, and actually try.
- **Historical `v0.0.1-research.*` tags:** archival snapshots created while bootstrapping the public research record; not the target user-distribution format.

The user-release contract is documented in [`release/README.md`](release/README.md).

## What is not proven yet

- Cross-platform generality beyond current Linux/X11 evidence.
- Production-grade automatic method discovery.
- End-to-end real model/token savings.
- Stable runtime/API semantics.
- A finished user-facing runtime distribution.

Python remains the experimentation vehicle while semantics are changing quickly. A lower-level production implementation comes after the algorithmic boundary stabilizes.

## Research discipline

Every promoted change should define H/T/D/C/U: hypothesis, minimum test, decision rule, competing explanation, and uncertainty. Correctness is a hard gate. Small noisy wins are not promotions. Negative results remain part of the record.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
