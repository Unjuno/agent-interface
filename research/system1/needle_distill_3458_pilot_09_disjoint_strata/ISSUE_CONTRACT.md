# Public treatment contract excerpt — Issue #4469

Source: https://github.com/Unjuno/agent-interface/issues/4469, fetched 2026-09-26.

The following T clause is copied verbatim from the public Issue body and is the binding treatment excerpt for this allocation:

> Use fresh paired seeds 3490, 3491, 3492; control and treatment remain as #4462. Treatment retains 1,024 balanced CORRECT rows, plus 512 band-A examples with signed |dx| in [.071,.110] and 512 band-B examples with signed |dx| in [.111,.149]. Each band must have an independent generator and explicit per-row audit checks that reject A/B crossover and the excluded gap; do not infer band correctness only from the pooled [.071,.149] envelope. Preserve other data bounds, model architecture, optimizer, steps, minibatches, evaluation suites and original quality gates. Add an issue-contract text/hash binding in the freeze and auditor.

The independent auditor hashes these exact UTF-8 file bytes against the digest pinned in `FREEZE.json` and validates each training row against its assigned band.
