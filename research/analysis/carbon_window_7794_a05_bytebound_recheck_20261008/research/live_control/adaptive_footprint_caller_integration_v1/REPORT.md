# Adaptive footprint local repair through shared caller v3 — retained local outcome

## Disposition

**PASS_SCOPED_INTEGRATION**. One frozen 30-case Inkscape/Xvfb block completed without retry. This is integration evidence, not shared-runtime promotion.

## Question

Can the existing `adaptive_acquisition_caller_v3` preserve ordinary stable warm reuse, while a no-authority footprint local-repair adapter recovers a visually moved target with zero model calls and refuses substitute/missing/duplicate appearances before task input?

Control and candidate use the same strong footprint reuse revalidation and the same final fresh revalidation. The sole arm difference is whether `association_changed` may enter one local-repair attempt. Model fallback is disabled in both arms. Persisted SVG state is scored only after the caller returns.

## Result

- Candidate: **15/15 condition-correct** independent SVG outcomes.
- Stable reuse: **3/3** candidate cases completed with `repair_path=none`; control also 3/3.
- Moved target + same-color decoy at the old location: control **0/3 task completion but 3/3 safe stop with zero task input**; candidate **3/3 correct target deletion via local repair**, zero model calls.
- Replaced-square, missing and duplicate conditions: candidate **9/9 SAFE_STOP with zero task input**; control also preserves the safe negative behavior.
- Wrong-target deletion: **0/30**.
- Model calls / model wait: **0 / 0** in every case.
- Input-owner release records: **496**, all verified empty. These are records, not independent reliability trials.
- Paired pre-controller current screenshots: **15/15 exact-byte-identical**.

Caller-stage median wall time was 654.868 ms for candidate and 539.721 ms for control. The arms perform different work and outcomes on moved-target cases, so this is descriptive only and is **not** a causal speed comparison.

## Important construction correction before the frozen block

An initial smoke incorrectly measured target freshness from the scene screenshot taken before homography computation. That made a normal stable case stop as stale. Before the formal allocation, the harness was corrected to the existing evidence ordering: scene observation -> scene projection -> **new target observation** -> footprint check. The 500 ms target freshness threshold was not relaxed. All source hashes were frozen only after this repair; smoke rows are outside the allocation.

## H / T / D / C / U

**H.** A no-authority footprint local repair inside adaptive caller v3 recovers moved targets with zero model calls while preserving stable reuse and refusing missing/ambiguous/substitute targets before task input.

**T.** 30 fresh Inkscape/Xvfb cases; 3 seeds x 5 scenarios x control/candidate; alternating arm order; persisted SVG is independent outcome oracle.

**D.** The frozen PASS rule was met. This does not promote the resolver into a shared runtime.

**C.** appearance is not semantic identity; shared caller integration may add freshness delay; moved target recovery may fail on larger displacement; post-click selection race remains separate.

**U.** Inkscape-specific fixture; three seeds; Xvfb timing; fixture-authored visual reference.

## Scope and next gate

The executed `adaptive_acquisition_caller_v3.py` is byte-identical to current-main Git blob `7faf042304728ce91a3e4f89d465b251ea0bf70d` at publication base `4e802fa2ec3c0c97545a38520bb18b3b126d8e4e`; the experiment does not patch that shared caller.

The visual reference is fixture-authored. Appearance remains evidence, not semantic identity. Post-click selection interference is a separate race studied elsewhere. Targets beyond the bounded search radius and scale/theme changes remain unsupported.

The next non-overlapping gate is scale/zoom robustness: keep the same caller authority boundary, compare fixed-scale footprint matching against a bounded multi-scale resolver, and require ambiguity refusal plus a fresh final revalidation before any input.
