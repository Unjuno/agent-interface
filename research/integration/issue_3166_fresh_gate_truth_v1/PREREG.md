# Issue #3166 — fresh commit-gate truth first rung

Allocation: `issue3166-fresh-gate-truth-rung1-20260926-01`.

## H / T / D / C / U

**H — Hypothesis.** When a prepared target/dependency remains current but its commit gate becomes FALSE, UNKNOWN, stale, cross-intent, or cross-epoch, `TWO_TIER_FRESH_GATE` refuses before physical input. `DEPENDENCY_ONLY` and `CACHED_PREPARE_GATE` admit at least one such case and produce an observable GTK effect. A native dispatch terminal without the declared application effect remains HOLD, never success.

**T — Treatment.** Source main at freeze: `27cb529f694609581c4a5b39e85ac782772e9aab`. The source pin set is recorded in `FREEZE.json`: public result adapter/API, selector, core contract, X11 backend/session, and GTK fixture. Use the current-main `runtime.cli_v1.golden_v3.dispatch_golden_v3` + X11 backend against that GTK3 fixture in one pinned, network-none OrbStack container. The cached image ID is `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, linux/arm64. Keep prepared dependency current in every row. Cross four explicit policy models (`TWO_TIER_FRESH_GATE`, `DEPENDENCY_ONLY`, `GATE_ONLY`, `CACHED_PREPARE_GATE`) over six contexts: current TRUE control, fresh FALSE, fresh UNKNOWN, stale TRUE, intent mismatch, and epoch mismatch (24 rows). Add one valid-gate GTK `no_effect` control (25 rows total). The independent raw-only scorer recomputes expected admissions and classifies the no-effect control. One formal outer container, then one isolated raw-only audit container. This first rung deliberately does not cover stale prepared dependency, malformed evidence, or duplicate commit; the full original issue remains open.

Policy definitions are frozen as follows: `TWO_TIER_FRESH_GATE = dependency_current AND gate_truth==TRUE AND gate_fresh AND intent_match AND epoch_match`; `DEPENDENCY_ONLY = dependency_current`; `GATE_ONLY = gate_truth==TRUE AND gate_fresh AND intent_match AND epoch_match`; `CACHED_PREPARE_GATE = dependency_current AND cached_prepare_gate_true`. The fixture/runtime dispatch executes only after the selected policy admits.

**D — Decisions.** `PASS_GATE_TRUTH_FIRST_RUNG_SCOPED` only if all four policies admit the valid control, TWO_TIER denies all five invalid contexts with zero runtime emissions/effects, DEPENDENCY_ONLY and CACHED_PREPARE_GATE each admit and cause at least one real effect in invalid contexts, GATE_ONLY denies all five invalid contexts, all admitted useful-mode dispatches have verified release and exact effect receipts, and the independent audit has zero errors. The valid-gate `no_effect` row must have a completed transport/native dispatch but no effect and be scored `HOLD_POSTCONDITION_UNOBSERVED`; otherwise the result is FAIL or HOLD. Infrastructure/source/image/audit failure is STOP, not a scientific result.

**C — Constraints.** Pin the current-main source hashes for `golden_v3`, API, selector, core contract, X11 backend/session, and GTK fixture before execution. Use only a disposable in-container Xvfb/GTK window, `/repo` and `/study` read-only, a fresh evidence mount, `--network none`, read-only root, bounded CPU/memory/PIDs, all capabilities dropped, no-new-privileges, and bounded tmpfs. No host display, user input, model/provider, credentials, GPU, or external network. No source/runtime modification.

**U — Unknowns.** This models the four admission policies in the frozen runner; current runtime does not expose a general commit-gate API. Intent/epoch mismatch are fixture-bound identity contexts. This does not test duplicate-commit idempotency, the full issue matrix, model decisions, production GUI safety, other backends, or integrated product behavior.

## Preservation / no-retry

Preserve #3166's reopened status, merged PR #3185, its XID replacement result, and every older allocation unchanged. This additive rung cannot close Issue #3166. Preserve the first formal outcome; no retries, replacements, pooling, threshold changes, or post-result edits.
