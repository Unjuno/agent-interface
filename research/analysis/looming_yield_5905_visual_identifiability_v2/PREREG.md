# Successor #5905 — image-only looming observational-equivalence boundary

Allocation: VISUAL-EQUIV-5905-S2-20261001-01

S1 was source-frozen at commit `8ad9071dd7f98724df51cf28cc095802bf959b37` but stopped before either formal invocation because its independent auditor did not validate the hidden truth-sidecar semantics. S1 remains unchanged and is not an observed scientific result. S2 is a new, additive allocation with a separately frozen audit gate; it is not a rerun or relabeling of an outcome.

Issue: https://github.com/Unjuno/agent-interface/issues/6030  
Predecessor: #5905 / merged PR #5920. Preserve its STOP_MAIN_ADVANCED_AFTER_FREEZE and NOT_EVALUATED outcome unchanged.

## H — hypothesis

If a physical approach and harmless sprite growth produce exactly the same timestamped raster stream, a deterministic cue restricted to those pixels and timestamps cannot yield on one and suppress a false yield on the other. This is an observational-equivalence bound, not an empirical claim about real imagery.

## T — finite execution

- Six matched pairs; 64×64 PGM frames; eight timestamps at 100 ms intervals.
- Each pair uses the same exact raster bytes/timestamps for two auditor-only worlds: physical approach with a declared contact time versus non-contact sprite animation.
- Contact/growth schedule varies over 760, 800, 840, 900, 1000 and 1200 ms.
- Candidate-visible compressed JSONL contains only opaque case/pair IDs, raster frames, dimensions and timestamps. Gzip storage is lossless and deterministic.
- One candidate invocation emits pixel-change, endpoint-radius-growth and radius-derived tau cues at a fixed 350 ms horizon.
- One separate raw-only auditor re-parses PGM, recomputes all cue outputs without importing candidate code, checks exact matched inputs and six complete truth pairs, requires each declared approach contact time to be later than the observed 700 ms horizon and each animation contact to be null, and runs four effective corruption controls including a mutated truth label.
- No random seeds; schedule and frames are deterministic. No retries, replacements, exclusions, threshold tuning or candidate rerun.

## D — decision

- PASS_VISUAL_EQUIVALENCE_BOUNDARY_SCOPED: six of six pairs have byte-identical observer inputs and different hidden contact truth; all three cue outputs are equal within each pair; at least one pair triggers a cue, necessarily also triggering on its animation counterpart.
- HOLD_CUE_NOT_TRIGGERED: invariance holds but no cue yields on any approach.
- FAIL_OBSERVER_LEAK_OR_INVARIANCE: output differs across an exact-input pair or candidate-visible input includes hidden truth.
- STOP_INTEGRITY: missing/extra/corrupt rows, invalid source identity or failed independent controls, including a truth-label mutation not rejected.

## C — controls

Candidate and auditor are separate programs. The candidate is given only observer_input.jsonl.gz; truth.json is a separate auditor-only input. Six schedules, all frame bytes and timestamps are compared exactly within their pair. Missing-output, changed-frame and changed-timestamp mutations must be rejected.

## U — limits

This only proves a boundary for the declared synthetic monochrome 2-D stream. It does not show that practical scenes are indistinguishable, or evaluate visual recognition, live DOOM, GUI behavior, actual contact, release, safety or product utility. An independently certified rigid-target/contact assumption may change applicability.

## Source freeze and launch gate

Freeze the source and inputs against one exact main SHA; publish their identity and read them back before the candidate run. Immediately before the single candidate invocation, refetch main and verify the frozen base remains an ancestor. If main advanced, inspect the comparison and proceed only when every changed path is disjoint from docs/CURRENT_GOAL.md, ROADMAP.md, docs/ISSUE_FAILURE_CLASSIFICATION.md, docs/RESEARCH_METHOD.md, predecessor #5905 sources/results, and this allocation path. Record latest main SHA and the complete changed-path list. Any overlap, Issue-scope change, branch-head movement or hash mismatch is STOP before execution. This path-scoped rule is predeclared to avoid repeating predecessor #5905's missed exact-main-refetch gate.

The test uses only the Python standard library on the local Windows host. Docker CLI daemon access did not respond, the computer-use surface exposed no Docker Desktop window or launch method, and shared Docker/OrbStack capacity is assigned to another worker; no container is launched and no shared slot is used.

## Formal commands

Construction (before freeze; does not run the candidate):

    python -m py_compile fixture.py candidate.py audit.py
    python fixture.py --construction-check

Formal fixture, one candidate run, then one independent audit:

    python fixture.py --out .
    python candidate.py --input observer_input.jsonl.gz --output candidate.jsonl
    python audit.py --input observer_input.jsonl.gz --truth truth.json --output candidate.jsonl --report audit.json

The candidate is invoked exactly once. Preserve the first result, including any STOP/FAIL/HOLD. The audit runs only if the candidate exits zero and output exists.
