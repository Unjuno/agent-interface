# Additive T2 gate-integrity correction for PR #5462

This is retained-input maintenance verification, not a new #5275 scientific
allocation. Exact original head: `6e320bf71ef4f7139a57d5cc60e7fa84a69b1597`.
Original raw SHA-256:
`a1db4a23028d91ce2dba0f92c62c24833678845df4721794cb7e8f1334087321`.
Preserve all original files, negative result, and verdict text byte-for-byte.

## Observed gap

Original audit_t2.py checks two gates against raw arm fields. It does not check
corpus_counts_fixed, exact gate keys, or Boolean types, and disposition still
depends on all submitted gate values. Unlike T1, empty gates are already
rejected. The original score/rate tolerance comparisons also lack finite/type
checks. These are audit completeness defects; they do not contradict the
original 8/8 supported abstentions and 2/8 OOD false passes.

## H / T / D / C / U

H: a T2-specific independently reconstructed gate map rejects inconsistent
gate metadata and nonfinite/numerically aliased values while retaining an
honest FAIL as integrity-valid evidence.

T: independently tokenize the pinned corpus and reconstruct the 16 rows,
three arm metric maps, and family counts. Reconstruct only these declared T2
gates: corpus_counts_fixed (16 rows/eight oracle-UNKNOWN),
combined_zero_ood_false_pass, and combined_iid_abstention_at_most_25pct.
Require exact keys and Boolean types. Derive verdict from reconstruction;
never import or execute candidate.py or run_t2.py. The CLI pins original
corpus and candidate hashes acquired through GitHub MCP.

Compare the original auditor and successor on the original raw plus five
finite metadata-copy controls: false count gate, missing count gate, extra
gate, integer one for the true count gate, and integer zero for a false gate.
All five are predicted to be accepted by the old auditor but rejected by the
successor; this does not predict that the original FAIL could become PASS
with unchanged rows and checked arm counts. Mutation change diagnostics use
canonical JSON equality, so integer and Boolean representations differ.

Eight test methods include original integrity-valid FAIL, attempted false
PASS, missing/extra/count gates, wrong Boolean types, nonfinite scores/rates,
row/denominator/family corruption, and a coherent synthetic PASS fixture.
That test-only fixture changes supported text to known vocabulary and OOD
text to unseen words with explicit matching row/aggregate outputs. It checks
that the verifier is not hardcoded to FAIL, and is not a scientific run.

D: maintenance PASS requires expected original-auditor counterexamples,
successor rejection of all five, eight passing test methods, separate CLI
exit zero returning integrity-valid FAIL_HELDOUT_LEXICAL_BOUNDARY for the
original raw, all frozen bytes unchanged, and independently reviewable
receipts. Preserve first FAIL/STOP without tuning or retry.

C: the old T2 auditor already validates two gate values and its current
negative scientific result is independently reproducible from retained text.
This correction improves metadata integrity; it must not inflate the finding
into T1's vacuous-empty-map defect or a false-PASS claim unsupported by T2.

U: synthetic hand-authored surface-disjoint descriptions, no population or
semantic generalization. No training/candidate/runner, model, network, GPU,
GUI, effect, runtime, or Docker execution. Declared side-effect zeros are
consistency checks, not independent observation of historical execution.
Duplicate JSON keys and malicious reference corpora are outside this repair.

## Execution boundary

Construction RED/GREEN remains separate. Reviewer approval precedes one
retained-input wrapper invocation. Before imports/calls, the wrapper checks
exact source head, complete eleven-file frozen hash map, and original raw
hash. It creates output exclusively and saves each control before assertions.
All originals and frozen code are rehashed after completion.

Budget: one-CPU affinity, RLIMIT_AS 256 MiB per process, CPU time 15 seconds
per process, outer timeout 30 seconds. This is not an aggregate cgroup memory
reservation; sequential parent/CLI processes briefly overlap. Record per-process
peak RSS, exact command/stdout/stderr/exit, hashes, and actual environment.

Planned repository-root command:

`timeout 30s python3 -B research/verification/ontology_gap_5275_t2_v1/gate_audit_v2/verify_retained.py --out <fresh-directory>`

Parent owns author-concurrency checks, remote publication, review and merge.
