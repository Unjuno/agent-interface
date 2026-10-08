# Prospective registration

Prospective A01 allocation — IR-visible alias boundary (not a rerun of consumed CEGAR allocations)

Owner: Codex thread 01a0b97b-0305-7f33-b0b4-01deb7c1d20c; branch research/5504-ir-alias-boundary-20261003; additive path research/analysis/verification_ir_alias_boundary_5504_a01_20261003/. Matching remote branch/alias PR and latest #5504/#5085 records checked; no competing owner surfaced for this path. Shared WSLc HOLD remains unchanged; no WSLc/Docker/GPU/model/GUI invocation or reservation.

Scope: implement the unexecuted method control proposed in comment 5937946951. Existing #5504 T0/T1/T2 and closed #4294/PR4298 results remain immutable. This is a new finite analytical allocation, not a portability rerun or a benefit claim. As docs/RESEARCH_METHOD.md allows, exactly determined expressibility is handled analytically first.

H: a required Boolean oracle has an implementation over visible predicates iff it is constant within every visibility-equivalence class. Opposite required labels in one class prove vocabulary insufficiency; repeated observations or a case-ID exception do not supply a missing semantic predicate.
T: predeclare 5 Boolean predicates (authority, current, effect_safe, dependencies_acyclic, reversible), all 32 valuations; PASS iff all five true. Restrict vocabulary to the first four, versus the predeclared complete five-predicate control. One frozen host modelchecker output and one independent read-only audit after construction tests; raw streams, exit codes, source/input hashes and first failures retained. The checker may inspect the modeled oracle for expressibility; no oracle-blinding claim. Pure tests and effective artifact corruptions are construction checks, not formal reruns.
D: restricted view has 16 fibers, exactly one conflicting fiber and no total correct Boolean implementation; diagnose ONTOLOGY_INSUFFICIENT and preserve both witnesses. Complete control has 32 singleton fibers and an exact table (31 FAIL, 1 PASS).
C: synthetic oracle and assumptions fixed by us; production Verification IR might already encode reversibility. This does not establish current IR incompleteness, CEGAR advantage over a complete static ontology, automatic primitive discovery, real safety, runtime/OS correctness, memory relief, or performance.
U: real primitive meaning, correctness of required dispositions, semantics/authority changes, model/GUI/timing and automatic vocabulary-extension authority remain outside this allocation. A reviewed real-IR predicate extension would require its own scoped work.

Stop: freeze/schema/integrity/audit failure ends this allocation; do not silently rerun it. No broad resource commands. Remote publication is batched after local tests and independent review; checked results only via PR.

Registration: https://github.com/Unjuno/agent-interface/issues/5504#issuecomment-5968198522

