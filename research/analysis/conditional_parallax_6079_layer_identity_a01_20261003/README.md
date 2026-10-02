# Conditional parallax layer-identity successor (#6838)

This additive package tests whether explicit, source-bound target/background track identity prevents the foreground-dominance false distinction retained under #6079 A01, while preserving two synthetic relative-motion positives. It is a method-only discriminator, not a repair or regrading of #6079.

Read PLAN.md and FREEZE.json before execution. The first attempted fixture was exposed to candidate helpers during construction and is retired; the frozen fixture is disjoint and construction tests use separate miniature cases. No formal candidate or auditor was launched at freeze time.

Candidate input: fixture/public.json. Auditor-only truth: fixture/auditor_truth.json. Candidate code: candidate.py. Independent raw-only auditor: audit.py (does not import candidate.py). Formal outputs must be new files under results/formal_01/ and are created exclusively. Exact commands and output hashes are recorded after the one-shot run.

Runtime is native host CPU/stdlib only because no isolated OrbStack slot was available. No GUI, model, game, OS input, network, GPU, or external effect is involved. This package cannot support a real-scene, contact, safety, task-benefit, or product claim.
