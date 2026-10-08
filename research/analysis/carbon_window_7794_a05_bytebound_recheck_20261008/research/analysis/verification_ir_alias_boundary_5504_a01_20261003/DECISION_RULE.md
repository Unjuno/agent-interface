# Prospective decision and stop rules

PASS_SCOPED_ANALYTICAL requires all gates below, not only producer exit zero:

1. Formal executions start only after independent source/proof review and
   construction tests/corruptions pass; sources, schema and predictions are
   frozen and their byte hashes rechecked before execution.
2. Exactly one formal modelchecker command completes with exit zero, no
   timeout, no interruption, no retry, COMPLETED attempt state, and raw
   stdout/stderr plus receipt are retained.
3. Exactly one independently authored read-only auditor checks those retained
   stdout bytes, completes with exit zero, and emits PASS/errors empty.
4. Restricted output retains case_030/case_031 with identical true,true,true,true
   visible evidence, FAIL/PASS labels, ONTOLOGY_INSUFFICIENT, 16 classes, one
   conflicting class, and no total decision table.
5. Complete predeclared control retains all 32 exact decisions (31 FAIL/1 PASS),
   32 classes, zero conflicts, EXPRESSIBLE; no case-ID predicate/exception.
6. Hash/readback integration checks reconcile frozen sources, original streams,
   receipts and audit input. No changed first result or erased failure.

Failure of a construction check permits a documented construction repair
before freeze, retaining the first failure. After freeze, any integrity,
launch, execution or independent audit failure closes A01 as HOLD/FAIL as
appropriate; preserve first outputs and do not repair/retry the allocation.
Expected ONTOLOGY_INSUFFICIENT is the negative-control result, not a runner
failure. Real corpus oracle/equivalence legitimacy remains NOT_EVALUATED.

Formal accounting names are explicit: host analytical modelchecker and
read-only auditor are one-shot allocations; pure fixture tests may exercise
their functions as construction only. Previously consumed CEGAR producers,
WSLc/Docker containers, GPU/model/GUI invocations and retry count stay zero.
PASS is a finite analytical criterion/control result, not empirical memory
relief, migration completion, production IR soundness, or roadmap completion.
