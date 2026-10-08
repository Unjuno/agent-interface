# Issue #7822 - bounded progress T0 A01

**Disposition: PASS_METHOD_SCOPED.** In this authored finite model, ordinary safety plus nonblocking admits a safe WAIT cycle that avoids the task marker indefinitely. The bounded policy reaches the marker in one transition on the positive case and three on the declared asynchronous path. It yields rather than promise progress when an adversarial uncontrollable cycle remains or marker evidence is unavailable.

## Results

| Case | Independent graph finding | Scoped result |
|---|---|---|
| Safe WAIT cycle plus marker action | Every reachable state can reach a marker; a reachable non-marker cycle exists; worst-case steps are unbounded. | SAFE_NONBLOCKING is weaker than bounded progress. |
| Bounded positive path | No non-marker cycle; every permitted path reaches an oracle marker in 1 transition. | BOUNDED_PROGRESS(1). |
| Declared asynchronous wait | Forced path tick, tick, progress reaches the marker in 3 transitions. | BOUNDED_PROGRESS(3), in event steps only. |
| Uncontrollable self-cycle with marker path | Marker remains finitely reachable, but environment can choose the uncontrollable self-loop forever. | PROGRESS_NOT_GUARANTEEABLE; safe yield; no fairness assumed. |
| Missing marker evidence | No independently evidenced marker exists in the graph. | SAFE_YIELD; no completion claim. |

The forbidden unsafe edge is not used. The checker rejected all five raw mutations: counting WAIT as progress, dropping the uncontrollable-cycle caveat, leaking oracle markers, assuming fairness, and enabling an unsafe transition. Full compact stdout, parsed raw candidate result, and independent metrics are retained alongside the exact source.

## H / T / D / C / U

- **H:** Supported only for the frozen graphs: finite-trace nonblocking permits a safe infinite non-goal cycle, while a finite transition bound requires excluding that cycle or stating environmental assumptions.
- **T:** The committed candidate produced the frozen traces once; a separately structured graph checker recomputed reachability, marker coreachability, non-marker cycles, worst-case distance, safety and trace evidence once.
- **D:** PASS_METHOD_SCOPED; audit errors are empty and five mutations are rejected.
- **C:** A basic safe-yield/no-progress handler may be simpler than a general bounded-progress supervisor. The candidate trace is authored for this fixture, so this does not establish a synthesis algorithm or improvement.
- **U:** Tiny finite authored graphs; no partial observation, user/model delays, GUI, real effect, or task oracle. Transition counts are not wall-clock guarantees; no fairness or physical environment assumption was tested.

## Environment and provenance

Source was frozen on branch `research/7822-bounded-progress-t0-a01-20261005` at commit `6e88656cd40ffcdce8bc733df9baf3631d0332c7`, based on main `4a8049327eb44b54cfcf55167adb102a710a7051`. Host CPython 3.11.9 executed the exact stored `t0.py` through stdin; C: had 0 free bytes, so no local/container writes were possible and WSLc was not used. Candidate and auditor each executed once; no retry. This is not a container-equivalent result.
