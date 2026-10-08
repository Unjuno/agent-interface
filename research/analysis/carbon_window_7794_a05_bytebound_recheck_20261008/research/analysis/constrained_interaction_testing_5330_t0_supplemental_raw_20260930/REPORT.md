# Issue #5330 — T0 constrained interaction-testing result

## Outcome

PASS_T0_SYNTHETIC_DESIGN for the explicitly declared deterministic finite model only. One candidate invocation completed. The first frozen audit stopped because its expected metamorphic denominator was hard-coded to 36 while the frozen pairwise array contained 9 rows and therefore generated 27 transformations. That audit STOP is retained unchanged. A separate corrected audit-only invocation examined the exact same raw bytes and passed; the candidate was not rerun or modified.

## H / T / D / C / U

### H — hypothesis
For this ten-factor synthetic workflow, constrained low-order interaction coverage and deterministic strength escalation discover more registered cross-factor hazards than one-factor-at-a-time while excluding dependency-invalid assignments. Unconstrained random chaos may spend runs on invalid cases.

### T — frozen test
The full binary space was 1,024 assignments with constraints: lost handoff requires active owner; duplicate retry requires delayed backend or lost handoff. Five deterministic hazard predicates were frozen. Methods: one-factor-at-a-time, constrained pairwise, constrained three-way, fixed-seed unconstrained random sampling (budget equal to three-way rows), staged strength escalation with deletion-minimization, and three metamorphic transforms over the first 12 available pairwise rows.

### D — observed results
- 640/1,024 assignments were valid; 179 feasible pair patterns were covered by 9 rows; 942 feasible three-way patterns by 20 rows.
- One-factor-at-a-time: 9 runs, 0/5 hazards found.
- Constrained pairwise: 9 runs, 4/5 found.
- Constrained three-way: 20 runs, 5/5 found.
- Unconstrained random, fixed seed 0x5330: 20 runs, 3/5 found; 10/20 assignments violated the frozen dependency constraints.
- Strength escalation: 33 unique runs, 5/5 found; 15 hazard observations were minimized with retained probe transcripts.
- Metamorphic transformations: 27/27 preserved classification (9 pairwise rows × 3 transforms).
- The fail-closed simulator recorded zero simulated and external effects. Independent raw-only audit rejected 4/4 corruption controls.

### C — controls and provenance
Every method used the same assignment space, constraints, five fault predicates, classifier, and no-effect simulator. Random selection used the fixed xorshift seed 0x5330 without replacement. Candidate source SHA-256: 980e31a5df3d824ea30a635457ebbed99c763d8e87c74fa600f71033732a6f0d. Raw SHA-256: ad6be24a2bd8789ffae8c9ef632c829c47813dab6477be6a324dd3c77363fec4. Corrected auditor SHA-256: 5e9245ef61bc6abfd135ba89d78367cffb70bdb0357b8b365360353da26649da. Base main: 1a27aff369ad1f690d4df6dc1664226ecc0726bb. No source/path overlap was found at intake; all files are additive on the dedicated branch.

### U — limits
The hazard rules are author-defined fixture truth, not observed frequencies or independently grounded failure mechanisms. This does not show that actual runtime failures are mostly pairwise/three-way, that unconstrained chaos is unsafe in deployment, or that a general locating array is effective. No live agents, GUI, actions, model/provider, GPU/CUDA, container, production authority, or task-quality/latency benefit was tested. The design and same-author oracle establish only a finite deterministic contract check, not real-system safety.
