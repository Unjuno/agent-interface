# Golden-v3: preserve both delivery evidence layers (#2441)

## Result and actual change

`PASS_GOLDEN_DELIVERY_JOIN_ENGINEERING` from one prospective 800-row local
receipt-contract allocation, 1,600 full adapter outputs, no formal retries,
replacement rows, exclusions or post-freeze source changes.

The current adapter selected `result.get("delivery", nested.get("delivery"))`.
An outer `confirmed`, `confirmed_partial` or explicit null could hide an inner
uncertain/unsupported/partial claim. The small `_delivery_evidence` resolver now
considers both same-contract fields before the existing mapping runs. This is a
shared runtime correction in `runtime/cli_v1/golden_v3.py`, with twelve permanent
regression methods in `runtime/cli_v1/test_golden_delivery_join.py`.

| Retained outputs | Original | Corrected |
| --- | ---: | ---: |
| All success mappings | 46 | 18 |
| Success despite ambiguous/unsupported delivery in either layer | 24 | 0 |
| Success despite partial delivery | 4 | 0 |

These are selected finite combinations, not actual delivery failure rates or
measured task outcomes. The two adverse rows below exemplify the correction:

- outer `confirmed`, inner `ambiguous`, completed positive receipt: formerly
  `success`, now `refused`, diagnostic `AMBIGUOUS_DELIVERY:ambiguous`;
- outer null, inner `write_uncertain`: formerly `success`, now `refused`.

Either partial claim, absent adverse evidence, remains partial. Both fields
unspecified preserves legacy behavior. Raw dispatch, partial effects, usage
availability and no-authority output remain intact. Refusal here is presentation
of unresolved evidence, not proof that an already attempted effect did not occur.
No retry or new action is granted.

## H / T / D / C / U

**H.** Considering both same-contract delivery fields prevents an outer
positive/null from hiding inner adverse evidence, while retaining compatible
single-source mappings and raw data.

**T.** Ten values per layer (absent, null, confirmed, confirmed_partial, five
ambiguity literals, future_state) and eight native/task/cleanup contexts: exactly
800 inputs, each mapped by the exact original and corrected functions. Contexts
are native positive, legacy positive, task false, unscored, nested refusal,
execution failure, runtime failure and cleanup failure. One runner process;
stdout, stderr, terminal record, command and actual zero exit are retained.
This is a deterministic finite protocol check, not a model or GUI experiment.

**D.** Every row and both complete output mappings must match a separately
implemented table oracle; raw input must remain unchanged; no adverse/partial
claim may map to success. Full denominator, source and process evidence and ten
effective raw corruption controls are required. Existing ten tests and twelve
new methods pass. The old adapter fails six of the twelve new methods; those
construction failure logs are retained, not relabeled.

**C.** Both fields mean delivery evidence for the same result, as in the existing
#2441 contract. There is no explicit supersession rule. Different stages needing
different semantics require distinct scoped fields rather than implicit outer
precedence. Unsupported > ambiguous > partial > confirmed > unspecified is the
conservative resolver order. Non-string values receive a typed diagnostic;
the twelve permanent tests also cover these outside the 800-row string/null
matrix. The existing downstream native/task/cleanup branch precedence is not
otherwise redesigned.

**U.** This does not prove actual delivery, application correctness, authority,
exactly-once effects, safe replay, producer authenticity, numerical confidence,
latency/token savings, cross-platform behavior or the whole #2337/#57 milestone.
One supplied Linux x86_64 container, CPython 3.13.5, stdlib only; Docker CLI and
image attestation were unavailable. Supporting package snapshots came from the
previous retained public-API study; current adapter and original test blobs were
checked against intake main. Only pure result mapping executes; no backend or
`.api.dispatch` is invoked. Current-head CI checks the real repository package
separately. The raw-only oracle is another implementation/process by the same
author, not independent human review.

## Chronology and preservation

Intake main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`.
Original adapter blob: `bd6e17310b176fd5e79b2a5197e74cfa7579aae5`.
Corrected adapter blob: `4009bf4b3b79b34936fa5fff800875b1f19a8b75`.

Issue #2441 owns this engineering continuation; it is OPEN, correcting an early
chat label. Its old results remain untouched. The preceding 12-case public-API
study was already merged by PR #4117 and was neither republished nor rerun.
Targeted Issue/PR/branch searches found no matching delivery-join owner; coverage
is bounded/non-atomic and says nothing about unpushed work.

Before the first formal process, commit
`06a812c3f3292db4c0cd7b83279f52dc99d68943` publicly committed FREEZE.json and its
nineteen source/plan/environment hashes; Issue comment 5832522733 records the
800-row schedule and exact command. This was a public hash commitment, NOT full
source publication. Source bytes were local before measurement and are all
retained in this publication. A relocation-path audit review correction was
made before that freeze, while formal output was absent. Frozen sources were
unchanged afterward. First result is Issue comment 5832532867.

- FREEZE SHA256: `be3e5b95bc4d5fde9b4fd1405a129ed4bc62d0d685d761acdbc0837b2db324c6`.
- RAW.jsonl SHA256: `3084c74c41334a6a76150d5676bebca2579fe83e4997aa3567bcceb599ce6840`.
- AUDIT.json SHA256: `b4ad197a9319b0baba395765da32a7d9ec53b5cf945cd300f590049fe216b69f`.
- Capsule SHA256: `fc826618decbd7b5314a4a137474c32c2a89049cdf173b6d5c217fc8b63dba8e`.

The ten parts preserve all 44 original source/raw/construction/metadata files,
1,243,413 member bytes. PACK.json binds ordered parts, expanded archive and
member denominator. Every uploaded part's Git object ID matched local bytes.
Postformal unpack/verify/test helpers and this README are publication additions,
not retroactively preregistered experiment code. Full PLAN.md includes the
conditional argument, variable table, unit check and exact source assumptions.

## Read-only reproduction

From this directory, in a trusted quiescent source directory:

```sh
python3 -S -B test_unpack.py
python3 -S -B verify.py
```

The six packaging tests include five refusals. `verify.py` restores to a new
temporary directory, runs the frozen raw-only oracle and both retained unittest
modules, and requires byte-identical original AUDIT.json. It never invokes
`run_matrix.py`. Manual restoration is also possible:

```sh
python3 -S -B unpack.py /tmp/golden-delivery-review
```

The destination must not exist. Restoration validates bounded compressed and
expanded bytes and extracts regular files without executing source. Checksums
are integrity commitments, not authentication or power-loss guarantees. Do not
rerun the consumed formal-01 allocation to review this change.

## Integration decision and delivery gates

This fixes a concrete result-presentation requirement in #2441/#2789; it does not
change input admission, lease, GUI policy or the original task scorer. No old
research path, foreign branch, global roadmap or existing workflow is modified.
The new offline CI reruns regressions and saved-data verification only. PR checks,
review, merge and exact-main readback are separate delivery gates recorded in the
PR discussion, never inferred from local PASS. Keep broader issues open.
