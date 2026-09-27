# Native direct / persistent primary comparison

This adds `--route direct` to `run_native_six_task_self_use_v1.py`; persistent
remains the default. Both routes share the six-task fixture, navigation,
independent saved-effect scorer and cleanup. Direct requests primary image
grounding per task and dispatches entry plus Save as one public native program.
Persistent retains its existing guarded references and single explicit repair.
There is no helper model, new sensor, guard relaxation or automatic retry.

This addresses the missing current-Native direct comparison in #2789. The
587-file archive retains both route allocations and both preceding construction
attempts. It is evidence for this composed path, not full integration acceptance.

| Measurement | Direct | Persistent |
| --- | ---: | ---: |
| Exact-once correct tasks | 6/6 | 6/6 |
| Primary grounding requests | 6 | 2 |
| Request-to-response wait, seconds | 170.580 | 50.164 |
| Cold capture through evaluator result, seconds | 174.982 | 56.500 |
| Median task execution through feedback, ms | 261.725 | 590.181 |
| Completed programs with verified empty release | 12 | 18 |

Both route runs used source 583ebb124f60743f085d58add47d1ca31604dc6d, seed991287,
the same Chrome-for-Testing executable and the primary conversation, in separate
private WSL GUI allocations. Persistent task4 refused the old layout before input
with zero emissions; primary viewed the replacement image and supplied one repair.
The first construction attempt on source90adbcf37 stopped at3/6 after consuming
its one repair early; its successor completed6/6 with a different field reference.
These predecessor rows are preserved separately, not pooled into this pair.

Primary waiting includes tool transport, polling, commentary and deliberation;
it is not inference-only latency. The cold-capture interval excludes initial
setup/navigation and ends before primary semantic confirmation. Persistent's
task4 execution interval includes repair waiting. Direct batches entry/Save;
persistent uses separate guarded calls. This is a sequential single pair, not a
randomized or replicated comparison. Model identity/configuration and environment
inventory were not independently retained before each run. Actual model usage,
cost, human reference and full descendant cleanup are unverified. Owner command
exit0 was observed in the conversation, not retained as a separate exit receipt.
No causal/general speedup, token reduction or PASS_INTEGRATION_SPINE_SCOPED claim.

## Running the comparison entry

Use system Python with the native GUI dependencies and `PYTHONPATH=.:research/live_control`.
Select `--route direct` or `--route persistent`, a fresh `--out`, a fixed `--seed`
and explicit `--chromium`. The runner prints each image and the requested JSON
path. View that image and publish its exact source_sequence plus field_point and
submit_point atomically; do not copy coordinates from this artifact or change
source while a run is live. Each request times out after300seconds. A nonzero
exit is a retained failed allocation, not permission to replay its inputs.

## Verification

`python runtime/results/native-paired-primary-01/verify.py` reads archived bytes
without extracting or replaying input. It checks hashes, independent saved
records, releases, refusal, timing arithmetic and the preserved predecessor fail.
The shared native CI runner now includes the direct program's invalid-grounding
regressions; 163 protocol plus68 harness tests passed locally. Full local logs
are under validation/. These tests do not establish GUI or performance generality.
