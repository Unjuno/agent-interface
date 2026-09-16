# Mindustry integrated persistent lifecycle mechanics v1

Task: `MINDUSTRY-INTEGRATED-LIFECYCLE-MECHANICS-20260917-001`
Issue: #851
Publication base: `488ecc39b6ede63d6f357ee52ed96be3df58552f`

Container-only deterministic integration mechanics. No model, GUI, Mindustry, X11, provider or task input.

H: separately versioned palette/world bindings plus one stable method can support cold -> reuse -> invalidation/refusal -> selective world repair -> post-repair reuse without stale authority or extra logical generations on reuse.

T: one seven-phase valid trace plus frozen negative controls. Cold and repair consume frozen injected artifacts and are charged as logical generation events only for accounting-shape mechanics. Reuse is locally revalidated and must charge zero. An independent auditor reconstructs transitions without importing the runner.

D: PASS only under Issue #851's exact invariants. This closes contract mechanics only; it cannot establish live Mindustry correctness, provider token savings, latency, or the matched three-arm economics still missing from #57.
