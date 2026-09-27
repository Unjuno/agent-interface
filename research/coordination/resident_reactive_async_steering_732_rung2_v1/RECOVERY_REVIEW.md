# Recovery review: Issue #732 Rung 2 predecessor HOLD

## H / T / D / C / U

**H** — Preserve the original one-shot finite-contract allocation as a distinct predecessor record. It must not be conflated with the later verified successor result published in `resident_reactive_async_steering_732_rung2_successor_01/` by merged PR #3758.

**T** — Recover the eight frozen source, preregistration, formal-result, and audit files from the abandoned branch. The source history and original result are retained byte-for-byte; this note records independent recovery checks only. No formal allocation was repeated.

**D** — The original report's `HOLD_SOURCE_HASH_NOT_PROPAGATED` is confirmed. Running its retained Python auditor against its retained 576-row `RESULT.json` under local Python 3.12 recomputed all 576 unique Cartesian cases, outcome counts, 10 stateful trace events, and eight invariants. It returned `FAIL` / `HOLD` only for `runner_source_sha256`: the result embeds `UNPINNED`, not the frozen runner hash. The independent JavaScript postformal audit and stored `AUDIT.json` report the same boundary. The frozen runner SHA-256 is `4d3899db4908fb0898a9c35e4ef075a9f478834420b85ef55b5e087b602fadc7`.

**C** — Host in-memory finite transition-contract analysis only. It is not container, runtime concurrency, GUI, model, performance, or product evidence. Docker unavailability and its environment limits remain as recorded in `RESULT.md`.

**U / lineage** — The harness passed the frozen runner hash as a Python global although the runner reads it from the process environment. The allocation is spent; this recovery does not repair, relabel, or rerun it. Merged PR #3758 contains a separate sibling successor with a valid scoped PASS; neither result supersedes or mutates the other. The original draft PR #3749 is only being superseded as a delivery vehicle by this recovery PR.
