# Issue 1178: structural baseline — retained first outcome

Task: `OPERATION-TARGET-STRUCTURAL-BASELINE-20260918-001`.
Decision: **HOLD_REPRESENTATION_NOT_SUFFICIENT_FOR_BACKEND_COMPARISON**.

## Actual container work

All development, source materialization, primary replay and audits ran in
`/mnt/data/experiment_1178_structural`, outside a repository checkout. The existing
released Issue/branch was taken over, rather than allocating a duplicate. This
is a pure standard-library synthetic retained-corpus study, with zero model,
training, GUI, task-input or shared-runtime actions.

The H/T/D/C/U and ROADMAP preceded implementation. Toy-only construction passed
7 fixed rule cases, 7 malformed cases, 10,000 identifier-renaming cases, and 12
copied-evidence mutation controls. Five upstream files matched both their Git
blob identity and SHA-256. Source publication/readback then matched 7/7 objects
and 18 archive members before the sole primary invocation.

Freeze HEAD: `3f2ddbe0f5f5d3054bb8e25f2eb645c8a2dfd093`.
Source archive SHA-256: `37174fcdae1890f94e30dfda2a7b95fd8c2fbf06ab1dcc16eab199915b9be73f`.
FREEZE SHA-256: `0e16576abcde032c7d4ed8878f064d57c6bf9639274c05755cdd428951af584b`.
Primary invocations: **1**. Reruns/replacements/post-result tuning: **0**.

## Exact retained input

The #1133 corpus was reconstructed with its original seed, not regenerated with
substitute examples. All 96 rows and 12 scenario units were retained; no labels,
rows or split memberships were edited. Both identities reproduce:

- semantic digest: `ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd`;
- CORPUS.json bytes: 146,377;
- exact CORPUS.json SHA-256: `d81b15cd7e7f9b0927aadfad3ce2e12e8dafe491d927ea275b291c799ac4f301`.

Reconstructing those bytes is not another #1133 formal allocation. No train or
held-out model was fitted; train/eval strata below are descriptive subdivisions
of an already-known fixed corpus, not new generalization evidence.

## First outcome

| Endpoint | All | Train | Eval |
|---|---:|---:|---:|
| Rows | 96 | 64 | 32 |
| Positive rows | 48 | 32 | 16 |
| Correct executable proposals on positives | 12 | 8 | 4 |
| Positive residuals | 36 | 24 | 12 |
| Negative rows | 48 | 32 | 16 |
| Negative false-executable proposals | 0 | 0 | 0 |
| Exact acceptable-set membership, all rows | 20 | 13 | 7 |
| Negative exact acceptable-set membership | 8 | 5 | 3 |
| Positive rows with absent required argument | 12 | 8 | 4 |

The rule correctly proposes SCROLL on 12/12 scroll rows. It withholds on all
other rows; the executable-positive coverage is 12/48 = 25%. The negative
false-execution rate is 0/48, but this must not be reported as 48/48 correct
semantic decisions. Generic safe YIELD is often not the declared expected
reason or NO_LOCAL_ACTION. Exact membership is only 20/96 overall.

## Three incompatible structural groups

Seven structural-signature groups exist. Three have an empty intersection of
acceptable-disposition sets, covering 64 rows:

| Same projected structure | Incompatible expected dispositions | Rows |
|---|---|---:|
| Two CLICK-capable buttons | CLICK either current target vs YIELD(AMBIGUOUS_TARGET) | 24 |
| One CLICK-capable button | CLICK current target vs YIELD(STALE_STATE) | 16 |
| No candidates; full operation vocabulary | NO_LOCAL_ACTION(ALREADY_SATISFIED) vs YIELD(MISSING_TARGET) | 24 |

For comparison only, target identifiers are alpha-renamed to their current
candidate slot; payload labels are abstracted while missing arguments are checked
separately. Operations, reasons, target slots and alternative sets are preserved.
Harmless target renaming therefore cannot create a false conflict. Exact proposal
scoring always uses original unmodified acceptable labels.

The other information gap is concrete: all 12 TYPE_TEXT positive rows advertise
`payload_ref_present=true` but their candidate packet contains no actual
`payload_ref` argument. The reference value exists in fixture/oracle data, which
the backend is forbidden to read or infer from identifier naming patterns.

Of 36 positive residuals, 24 are in incompatible CLICK groups and 12 lack the
payload argument. No residual in this allocation establishes a need for a more
capable learned backend.

## Audit and integrity

The frozen read-only independent auditor imports neither the candidate nor the
upstream generator/oracle/validator. It reconstructs authored oracle outcomes,
projection signatures, normalized acceptable sets, proposals, grouping, residuals,
and all/train/eval statistics. It agrees on the HOLD; errors are empty. The 12
preregistered evidence corruptions are all rejected. All 17 frozen source/plan/
control members are unchanged after primary. The primary process exited 0 with
empty retained stderr.

- RESULT.json SHA-256: `b48ace3bf9c2a83b26c093af3418a352b39904efac14cbbefceadf381a9cfb8f`;
- AUDIT.json SHA-256: `b8e98e2a27b1229f5b6902e2fae51fe7c4a2a221b5f6be12e9ada1e4b8285c5a`;
- CORRUPTION.json SHA-256: `6b0acfdc43481e8afb54589cf6131eecb980fd1bcc1220b865de1312eca7c763`.

The primary reconstruction/scoring/file-output region took 8,183,078 ns on this
CPython 3.13.5 container. This is descriptive execution accounting, not a warm
latency benchmark or performance comparison.

## Limits and coordination

This conclusion applies to #1178's explicitly restricted identifier-independent
projection. Full packets have different literal observation/target IDs; we do not
claim they are byte-identical or prove impossibility for every possible richer
representation. A deterministic function of the frozen projected signature cannot
satisfy mutually disjoint acceptable sets; a learned function of the same signature
cannot add the absent distinction. Safe abstention remains possible, but is not
necessarily the exact semantic answer.

The generator, oracle semantics and source schemas were already visible before
this study. This is a scoped sufficiency diagnostic, not blinded discovery. An
independent audit implementation is not an independent real application oracle.
No live task effect, model competence, productivity, token saving, or production
safety claim is made. #1133's original data-contract result is preserved unchanged.

A coordination comment received during construction reports #1177/PR #1184's
separate target_admissibility experiment. Its features were not added to this
frozen allocation. That work uses a different projection/counting unit; its 28
conflicts must not be pooled or equated to our three structural groups. Future
integration should reuse that existing lane rather than repeat it. Actual caller
payload-reference plumbing is the additional gap exposed here; test that in a
separate scope before any model allocation. Stop this allocation now.

## Retention

The publication contains a fully recoverable frozen source archive and a separate
lossless results/corpus archive with a read-only reconstruction helper. All 96
corpus rows, all 96 output records, all seven groups, audit, corruption receipts and
primary invocation receipt are retained; no corpus row is only a claimed digest.
The conversation ZIP additionally provides directly readable files and a manifest.
