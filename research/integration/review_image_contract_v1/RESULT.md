# Result: shared review image-content qualification

## Disposition and chronology

**PASS_REVIEW_IMAGE_QUALIFICATION_SCOPED** for allocation
`review-image-qualification-20260922-01`.39/39 fresh case processes,9/9 batch
supervisors observed exit0, no formal retries/replacements/source edits. Local
preregistration only; remote Issue/PR/source freeze did not exist before execution.

Current shared review modules are byte-identical to source main
`2308b8301d69b7089a2e0636486736ed59b61537`. Preformal main advanced to
`33e86e997d02b769af17a3f03f6035c68927da6e`; review.py retained the same blob.
This is an opt-in content-qualification experiment, NOT a new production default,
full CLI/MCP invocation, native task, source authenticity guarantee or host image
presentation measurement. Original `image_status=image` continues to mean delivery
of selected bytes; it is not retrospectively declared a full decoder certificate.

## H/T/D/C/U

H: matching image hashes/signature do not establish decodable content or matching
recorded geometry. A separate read-only stronger gate can withhold unsupported image
payloads without erasing original partial/recovery/release fields.
T:13 controlled report conditions x3 existing callable paths (file review, received
bytes review, shared present_result), original plus qualified presentation for the
same invocation. Five complete upstream modules unchanged; namespace package loading
avoids the unneeded package .api initializer. Compact/report-reference modes off.
D: all declared39-case and process/source/byte/outcome gates passed; full raw-only
independent implementation returned no errors;12 coherent semantic mutations rejected.
C: cooperative quiescent synthetic reports/images, static RGB/RGBA PNG, declared
small decoder envelope. No cache maintenance or concurrent file changes. A validity
flag is not authentication/currentness; a historical failed release remains recorded.
U: dependency cost, wider PNG modes, real host/render/model/task effects, arbitrary
concurrency and production integration untested. No speed, token or reliability-rate
claim. Same-author separate audit implementation/process is not human peer review.

## Finite result table

Each cell lists the number of callable paths exhibiting the result (3 total), not
population repetitions. All reports are synthetic; completed/partial/release fields
are test inputs, not real executed outcomes.

| Condition | Exact current reviewer | Added decode/geometry gate |
|---|---|---|
| VALID_RGB | image,3 | decoded geometry match,3 |
| VALID_RGBA | image,3 | decoded geometry match,3 |
| LOSSLESS_REENCODED | image,3 | decoded geometry match,3 |
| SIGNATURE_ONLY | image,3 | content HOLD,3 |
| TRUNCATED_IDAT | image,3 | content HOLD,3 |
| BAD_CRC | image,3 | content HOLD,3 |
| WRONG_GEOMETRY | image,3 | content HOLD,3 |
| MISSING_DIMENSIONS | image,3 | content HOLD,3 |
| BOOLEAN_DIMENSION | image,3 | content HOLD,3 |
| DIGEST_MISMATCH | needs_review,3 | original refusal preserved,3 |
| MISSING_FILE | needs_review,3 | original refusal preserved,3 |
| NO_OBSERVATION | no_observation,3 | unchanged,3 |
| VALID_OTHER_PIXELS | image,3 | decoded geometry match; origin unverified,3 |

Original totals:30 image,6 needs_review,3 no_observation.
Candidate:12 decoded/geometry matches,18 content HOLDs,9 not-evaluated upstream
refusal/no-image conditions. Thus18 returned byte payloads are not qualified under
the stronger declared content contract:9 structurally invalid PNGs and9 missing,
malformed or mismatched dimension declarations. This does not allege18 real host
failures or18 historical task errors.

All39 receipts/outcome summaries were unchanged; all18 synthetic partial, recovery
required and failed-release cases remain partial/required/failed. Accepted image
bytes were not re-encoded. A secondary cross-route read-only comparison confirmed
all13 cases have equal image payloads, outcome summaries and qualification decisions
across the3 callables; full responses differ in legitimate source/path provenance.

## What the counterexample establishes

The8-byte PNG signature with its own correct SHA256 passes the exact review's
hash/signature checks. It lacks PNG chunks and pixels. The added gate rejects it
without altering the recorded action/result. A13x10 valid PNG with16x12 declared
size similarly remains decodable yet fails the geometry gate.

Conversely, the valid-other-pixel fixture has the same dimensions and a self-consistent
encoded hash but differs from the nominal capture bytes. The candidate accepts its
format/geometry in3/3 routes and explicitly leaves origin/currentness unverified.
Neither proposed validation nor hash equality supplies the missing capture binding.

## Integrity / ERROR CHECK

-16 frozen source/plan/environment entries rehashed exactly.
-5 upstream full-module Git blob IDs verified on materialization.
-39 actual worker exits0 and9 actual batch exits0; all stderr empty for formal actors.
-Independent auditor imports neither Pillow nor candidate/runner/vendor code; PNG
  CRC, zlib extent, five filter modes, geometry and every returned decision recomputed.
-12 coherent output mutations reject after stdout hashes are recomputed, including
  accepting signature-only data, false geometry, erased partial/release fields,
  authority/origin promotion and changed decoded evidence.
-10 unit tests pass; no formal rerun to obtain a passing auditor.
-FREEZE SHA256:`f5b13ffff22416e1236b92adb1751e1979f96d1a180f07c84d6a8da74d2bdfaf`.
-AUDIT SHA256:`4532716351f4c32d314b4121ea40c73422feef753c805d5492c57d56910faa26`.

## Preserved construction limitation

The first13-case construction orchestration hit its20-second supervisor bound
with10 complete worker receipts and an incomplete next case. Its original unknown
supervisor returncode, bytes and source copies remain under construction-01. A
post-stop inventory found no study actor; no missing exit is reconstructed.
Before any formal allocation, construction was divided into5/4/4-case groups;
construction-02 completed all13 excluded9x7 cases with the same candidate.
Formal source/plan hashes were fixed only after that correction and10 passing tests.
This is a retained local engineering event, not a scientific failure or separate issue.

## Reproduce audit only

From this directory, with Python3.13.5 and the supplied files:

```sh
python -B audit.py formal-01 > /tmp/review-image-audit.json
cmp AUDIT.json /tmp/review-image-audit.json
python -B audit.py formal-01 controls > /tmp/review-image-controls.json
cmp CONTROLS.json /tmp/review-image-controls.json
python -B -m unittest -v test_contract
```

The first two commands need only stdlib. Unit tests/candidate require Pillow12.3.0,
LOAD_TRUNCATED_IMAGES=False. Do not rerun execute.py on a consumed output. A new
allocation needs its own prospective freeze and explicit reason, not repeated trials
until an agreeable result appears.

## Environment, publication and next decision

Provided Linux x86_64 container, CPython3.13.5, Pillow12.3.0, Intel Xeon Platinum8370C guest,
uncontrolled clock frequency/load. No Docker/OrbStack image identity or attested
network-none boundary. No installations, model/provider, GUI, user desktop/input,
actual task effects or experiment network traffic. Monotonic timings are diagnostics.
No combined timing uncertainty or coverage factor estimated.

This session has no GitHub write/comment action exposed; direct GitHub DNS failed
and gh is unavailable. Remote mutations0. Publication is LOCAL_ONLY_PENDING_REVIEW,
not main integration. The additional git patch is checked in an empty local directory,
not against a real main checkout. Required CI/human review remain unexecuted.

For #3544/#3711/#2789, retain the distinction between selected file bytes, decoded
image metadata, original execution result and actual model-visible useful feedback.
A later adoption decision should test a real host image consumer and bound decoder
cost/support; it must not add action replay or treat content validation as input
permission. The global ROADMAP remains open; no parent Issue is closed here.
