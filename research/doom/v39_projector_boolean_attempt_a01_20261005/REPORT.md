# V39 projector boolean attempt-ordinal probe A01

**Disposition:** `FAIL_METHOD` on the frozen current-main projector; narrow schema finding only.

## H / T / D / C / U

- **H:** `_valid_pair` may treat JSON boolean `true` as integer attempt ordinal `1` because equality accepts Python's `True == 1`, unlike neighboring exact-type numeric checks.
- **T:** With the frozen current-main helper and existing singleton fixture, evaluate one untouched positive control and one candidate that changes only `server_keyup_attempts[0].attempt` from integer `1` to boolean `true`. Run the existing unit class as context. Candidate retries: zero.
- **D:** Candidate ready despite exact JSON integer requirement => `FAIL_METHOD`. Rejection with accepted control would have been `PASS_METHOD_SCOPED`.
- **C:** Synthetic malformed-JSON/schema check only. Does not establish release behavior, application consumption, physical key state, or suitability of the projector on real V12→V4→BatchBackend records.
- **U:** One frozen helper/fixture and one mutation. No live game, GUI, OS input, model, service, or container. Host Python/stdlib only.

## Frozen source and fixture

Main commit: `f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c`

- Helper `research/doom/project_v39_release_measurement_v1.py`, Git blob `3683534757f55cbc2c60b1ce2cde7a0847c3f090`.
- Fixture/tests `research/doom/test_project_v39_release_measurement_v1.py`, Git blob `28e34663420af31642f8826f0f53385327872be6`.

## Raw outcome

The wrapper setup initially stopped before candidate execution because `TextEncoder` was unavailable in the orchestration JS runtime. The wrapper was changed to URI encoding and the candidate was executed once; this was not a candidate retry.

```text
POSITIVE_CONTROL_READY True
CANDIDATE_BOOL_ORDINAL_READY True
INDEPENDENT_EXACT_TYPE_ADJUDICATION False
Ran 4 tests in 0.000s
OK
EXISTING_SUITE 4 failures 0 errors 0
```

Independent adjudication used `type(value) is int`; the mutated value is boolean, so it fails the exact JSON integer requirement. The original projector nevertheless returned `measurement_ready=true`.

## Follow-up and coordination

A minimal exact-integer predicate and regression were added to Draft PR #8132; its branch suite then passed 6/6. After that, a concurrent #59 worker disclosed a broader repair of this same projector (one-to-one identity matching and compatibility against actual V12→V4→BatchBackend rows; #59 comment 5991451464). This probe was not repeated. PR #8132 remains Draft and must not be independently integrated without comparing/subsuming it into that broader repair. Preserve this report and the original finding even if the code patch is superseded.

Issue record: #59 comments 5991435309 and 5991452452.
