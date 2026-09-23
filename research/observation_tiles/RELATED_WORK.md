# Related work for observation tiles

Checked 2026-09-13 JST. This bounded design review records what primary sources support for the next observation experiment. None of the cited external benchmarks measures lossless visual deltas, image-token savings, or a faster model loop.

## Evidence and decisions

| Source | Verified evidence | Adopt | Hold / limitation |
|---|---|---|---|
| [OSWorld paper](https://arxiv.org/abs/2404.07972) and [repository](https://github.com/xlang-ai/OSWorld) | 369 tasks in real web/desktop apps, initial-state setup, interactive execution, custom execution evaluators. The public `lib_run_single.py` runner saves a screenshot after each environment step and applies configurable post-action sleep. | Reproducible setup, per-task artifacts, action traces, independent final oracles; paired fixed model/task/environment comparisons. | Whole screenshots only; no observation-policy counterfactual. Real desktop rollouts establish task capability, not tile transport or token savings. |
| [AsyncTool](https://arxiv.org/abs/2605.27995) v3 and [code](https://github.com/StoKou/repo-asynctool) | Interactive multi-task tool use with simulated tool-specific latency, delayed/out-of-order feedback, dependency-constrained calls, step/subtask/task metrics and efficiency metrics. Data trajectories are validated and model reconstruction is manually checked. | Explicit sequence/timestamp IDs, pending-result state, stale/out-of-order handling, and separate completion from waiting. | Simulated latency and task composition; no live GUI capture or desktop rendering. Treat as temporal stress methodology, not screenshot evidence. |
| [WeaveBench](https://arxiv.org/abs/2606.09426) v3 | 114 long-horizon tasks on a real Ubuntu desktop in deployed runtimes, screenshot plus nine GUI primitives alongside CLI/code. Tasks require non-substitutable GUI/CLI phases and cross-application state. A trajectory-aware judge re-fetches files, images, logs and traces. | Long-horizon probes, trajectory logging, evidence re-fetch, and process-aware scoring for later validation. | PassRate does not isolate exact equality or tile deltas; separate agentic judging remains evaluator uncertainty. |
| [Agent Interface A1 report](../observation_gating/REPORT.md) | Exact byte equality preserved correctness and 1,446 sampled-frame reconstructions across 96 paired tasks/four real apps, with 17.15% same-trace image reduction. | Retain as prerequisite baseline; extend exact reconstruction and stale/missing-base tests to tiles. Keep capture pixels, forwarded pixels, model-visible images, tokens and latency separate. | Live scripted Linux/X11 receiver, zero model calls; sampled pixels only, no model compatibility or rare-failure bound. |

## Tile protocol boundary

A fresh stream must begin with a full base image. Every later observation should
carry a monotonic sequence number, action ID, capture timestamp, and base
reference. The receiver must reconstruct the exact current image before model
delivery. Missing, stale, reordered, malformed, or dimension/mode-incompatible
bases must fail closed and request full resynchronization. A delta is useful only
when it is lossless under this contract.

Report task/final-oracle correctness, reconstructed-image equality/continuity,
candidate/forwarded image and pixel counts, and local component/first-feedback
timing independently. If a model adapter is added later, measure model calls,
serialized image bytes/tokens, resume time, retries, and end-to-end latency as a
separate live condition. Include local edits, large redraws, scrolling,
cursor/caret changes, window movement, and app/process replacement; include a
cross-application or long-horizon workload before runtime promotion.

Do not make perceptual similarity, hash-only gating, or an unverified crop the
correctness path. Do not treat a similar frame as proof that no relevant event
occurred between captures. Do not claim model-token or API-cost savings from
forwarded-pixel reduction: OSWorld does not establish downstream tokenization,
A1 had no model calls, AsyncTool delays are simulated, and WeaveBench varies
models/runtimes. Such a claim requires a fixed model/API adapter and paired
model-in-the-loop evaluation.

## Evidence boundaries and uncertainties

OSWorld and WeaveBench execute real desktops but publish capability/methodology
results rather than observation-transport ablations. AsyncTool informs delayed
feedback and dependency methodology, but its latency environment is simulated.
WeaveBench's judge is model-based. A1's zero sampled reconstruction errors do
not cover arbitrary displays, capture intervals, remote links, hardware cursors,
hidden nonvisual state, or whether a model understands base-plus-tile input.
The tile study needs its own freeze, fresh replicates, exact audit, and model
visible compatibility check. Cross-platform behavior beyond Linux/X11, remote
recovery, and genuine API image tokenization remain open.

## Sources checked

- OSWorld repository README and current `lib_run_single.py` (screenshot-per-step logging and post-action delay).
- Xie et al., *OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments*, arXiv:2404.07972v2.
- Shi et al., *AsyncTool: Evaluating the Asynchronous Function Calling Capability under Multi-Task Scenarios*, arXiv:2605.27995v3, plus linked code.
- Li et al., *WeaveBench: A Long-Horizon, Real-World Benchmark for Computer-Use Agents with Hybrid Interfaces*, arXiv:2606.09426v3.
- Local [A1 report](../observation_gating/REPORT.md) and repository README.

Elapsed time was not instrumented, so no timing comparison is reported. Uncertainties are details not exposed by cited abstracts/repositories, such as provider-specific image-token accounting and exact live GUI capture timing.
