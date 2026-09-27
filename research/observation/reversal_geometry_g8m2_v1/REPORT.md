# #4387: unequal-interval reversal inference

**PASS_UNEQUAL_INTERVAL_APPLICABILITY_SCOPED. Research evidence only.**

One360-case deterministic synthetic allocation completed once, with1080 outputs, actual process exit0 and no timeout, rerun, replacement, tuning, model call, training or GUI/input. The exact legacy heuristic is a research-branch helper, not production runtime. No predecessor outcome is changed.

## Question and first-outcome result

Hold three timestamped observations, speed73px/s, unknown absolute offset and1px point-error bound fixed. Query right-hand direction at the newest sample itself. Compare the unchanged #4255 full-displacement heuristic, an exact-rational transcription of the same logic, and continuous one-reversal set membership. No extra frame, post-newest tail, unknown timestamp, acceleration or extra reversal is introduced.

| Method | Correct | Wrong | UNKNOWN | Total |
|---|---:|---:|---:|---:|
| Legacy Python float |146|26|188|360|
| Same heuristic, exact rational |146|26|188|360|
| Continuous feasible-direction candidate |120|0|240|360|

The float/exact diagnostic disagreed0 times. Every wrong legacy direction has two opposite-direction compatible worlds for the same input. The candidate also removes26 correct legacy proposals and adds0 correct proposals. Thus this is a supported-model soundness result, not a claim of improved task utility or coverage.

Each geometry has60 cases. Columns below are correct/wrong/UNKNOWN.

| Newest / preceding interval (ms) | Legacy | Candidate |
|---|---|---|
|100 /100|28 /0 /32|28 /0 /32|
|100 /10|26 /8 /26|8 /0 /52|
|10 /100|16 /18 /26|8 /0 /52|
|100 /25|24 /0 /36|24 /0 /36|
|25 /100|24 /0 /36|24 /0 /36|
|40 /160|28 /0 /32|28 /0 /32|

Zero errors in four finite strata is not a proof that the legacy heuristic is sound for those geometries generally. These deliberately selected trajectories/errors are not a deployment distribution; counts are not reliability probabilities. The unit of evaluation is a synthetic source triple, not a GUI session or model call.

## Two retained counterexamples

Case120: true constant LEFT motion, source times0,-10,-110ms, observed positions100,100.73,108.03px, with only binary64 serialization roundoff. The newest displacement -0.73px fits both +0.73 and -0.73 within2px, whereas the preceding interval clearly fits LEFT. Legacy treats newest ambiguity as a reversal and returns RIGHT. Candidate returns UNKNOWN with compatible constant-LEFT and reversed-RIGHT witnesses.

Case65: true latest direction LEFT after a reversal1ms ago; source times0,-100,-110ms, observed positions100,92.846,92.116px. The newest +7.154px displacement fits nominal RIGHT travel7.3px while the preceding0.73px interval is ambiguous. Legacy returns RIGHT. Both directions have compatible full trajectories; the candidate refuses to infer a unique direction.

Actual inputs are stored as binary64 hex and rational true positions. The proofs/witnesses use exact rational interpretations of those retained bits, not the rounded decimal examples printed here. No function of identical observations can universally select one direction when two allowed worlds remain feasible.

## H / T / D / C / U

H: unequal intervals can defeat the published two-full-interval heuristic despite correct source time and bounded point error; all-world compatibility distinguishes unsupported certainty from informative observations.

T: six fixed interval geometries, two directions, constant plus five reversal ages, five fixed point-error patterns;360 synthetic triples. A single formal process consumes a published corpus and emits three outputs per triple. Candidate sees only records, never truth labels or scenario names. Eight disjoint construction unit methods cover arithmetic, malformed input, epoch/order and incompatible data. No live predecessor is rerun.

D: complete360/1080 provenance, a supported unequal-interval legacy counterexample, exact candidate/independent-vertex agreement, true direction in every feasible set, zero wrong singleton decisions, at least one singleton, preserved frozen files and8 effective semantic corruption rejections. All are observed. Overall PASS rejects blanket promotion of the legacy heuristic; it does not assert its old fixed-corpus results were false.

C: both methods assume a very restrictive known-speed/at-most-one-reversal family. Ambiguity becomes more likely when travel is small relative to observation uncertainty. A singleton is conditional on this family and error bound, not semantic understanding or permission. Declared right-hand endpoint convention includes reversal exactly at the query.

U: unknown real sensor bounds, motion-class violations, stale/foreign lineage, future action-time direction, independent human review, practical task utility, cost/latency and cross-platform behavior remain untested. No calibrated statistical uncertainty or coverage factor is inferred from exact rational finite checks.

## Proof and audit

PROOF.md contains the complete conditional family-coverage, affine-elimination, independent bounded-polygon-vertex and abstention-soundness argument, with variable/domain/type/unit table and dimension check. The solver continuously solves reversal time and unknown offset; it does not discretize reversal time. All directions have explicit witness worlds. The auditor separately enumerates polygon boundary intersections using rational arithmetic, imports neither solver nor runner/legacy, and validates every witness against the three observations.

Original audit errors=[]; eight effective, well-formed copied-row changes were rejected with parser_crashes0. Changes cover missing row, identity, decision, feasible directions, authority, legacy output, rational diagnostic output and witness offset. All13 frozen files rehash unchanged. Actual formal, audit and controls subprocess PID/argv/start/end/zero-exit receipts are retained. The eight construction methods passed before source publication. Same-author separate implementation/process is not independent human review. The frozen audit uses assertions; do not execute under Python -O.

Rows SHA256:0649dcb4a6db74bb34bae3e16d39bc463fa7398679bd96668600505124597ed4.
Audit SHA256:028d9e9970e01b65b37980e729961fd637341d56269e20bafc4f93f10292153a.
Controls SHA256:6b2ab03c12b338807e5401c58c6dd7407c8b97e925c89af728fd00058a294c87.

## Chronology and actual environment

Intake main4c701cc51b06296268ad8d9ae3eff1dd6f2d379d. Source/corpus commit818f8f60313a3908ba93995ab558baec31125f00 and Issue#4387 preceded measurement. All14 preformal files, including the full360-case corpus, were publicly preserved in a lossless source capsule and read back by nine file Git identities. Preformal comment5841183992 precedes execution; first-outcome comment5841192058 precedes result packaging. FREEZE SHA256:e5b99102920575a6401f80dcf5c47e0ea4dc33470264e4602dcf46a73e44debb.

Provided Linux6.18.44 x86_64 container, CPython3.13.5, standard library/Fraction, guest Intel Xeon Platinum8573C, five allowed CPUs, no pinned affinity or controlled clock frequency. Docker/gh CLI unavailable, no Docker/OrbStack image attestation. No package installation, credentials, external experimental network, model, GUI, action or shared-runtime mutation. This was mathematical/implementation validation, not a wall-clock capture experiment or performance benchmark.

The previous conversation's incomplete source-age live allocation is not repeated or reclassified. Only the exact prior legacy helper was recovered from its archive and checked against current Git blob eda3a4922b02b58e76a907e0e239b220502cf7c3. No prior full archive is represented as published by this study.

## Integration boundary

Publish only under research/observation/reversal_geometry_g8m2_v1/. No existing runtime, workflow, index, prior evidence or foreign branch is modified. The evidence supports an applicability requirement before future direction-to-effect integration, not a drop-in production solver. No task-effect or timing gate is claimed. Parent#2442/#4255/#2542 and repository ROADMAP remain unresolved. CI, review and merge are separate delivery gates to inspect at the exact PR head; a local numerical PASS is not a repository-wide test result.
