# Post-return clock failure: acknowledged-update successor

## H/T/D/C/U

- **H**: If `advance_action()` returns but reading its return timestamp fails, V1 classifies the update as unavailable and loses the fact that the client call returned. The update-call result, timestamp qualification, tic qualification, and scorer sample availability are separate facts.
- **T**: Preserve the exact #7554 head (`9e33a99e495b148f9dbfa90fef16413859b271de`) unchanged. Reproduce the second-clock-call exception using a fake game; develop an additive V2 candidate and test that the returned-call fact survives without fabricating a return timestamp or `tic_after`. Keep failed-update/no-retry and predecessor packet integrity checks, then verify independently on latest main (`c7837e7aae09bf2f3d9b40a77b790d7d6777d799`).
- **D**: Baseline TDD reproduction failed as expected: one `advance_action` returned and advanced tic 7→10, then the second `clock_ns()` call raised `OSError`; V1 emitted `UPDATE_UNAVAILABLE` and no producer. A second red test found that V2 redundantly re-read the clock instead of reusing an already observed external ACK; the final candidate reuses the wrapper's full timing/tic bracket. The additive V2 tests pass 6/6 on both the exact #7554 candidate and latest main. The V2-injected suite passes every unaffected existing scorer contract (10/10 on #7554 source; 9/9 on latest main); its old no-op assertion is deliberately replaced because V2 now distinguishes API return from failed tic advancement (`UPDATE_VALIDATION_FAILED`, not `UPDATE_UNAVAILABLE`). A dedicated V2 no-op test passes. The unmodified V1 suite passes 11/11 and 10/10, respectively. The #7554 packet audit passes with 13 manifest files.
- **C**: Native Python fixture-only construction. This establishes the client method returned in the fake and preserves that fact in the sidecar model. It does not prove engine acceptance, tic advancement in the failing-clock path, timed observation, scorer availability, runtime integration, or live control. V2 is not yet selected by V16.
- **U**: Integrate the candidate through a reviewed V16 opt-in successor, including its import-time class binding, while retaining the V1 packet unchanged; run all regression suites in a hash-pinned container, then independently audit it. Any live qualification remains separately gated by current roadmap allocation and threat-exposure evidence.

## Executed checks

- TDD red on the exact #7554 working-tree source: targeted test failed because `UPDATE_UNAVAILABLE != UPDATE_RETURNED` after one successful API return.
- TDD green: `PYTHONPATH=research/doom:research/doom/acknowledged_scorer_status_clock_v2_59_20261004 python3 -m unittest -v test_acknowledged_scorer_clock_v2` — **6/6 PASS**.
- Existing V1 suite: **11/11 PASS** on #7554 source; **10/10 PASS** on latest main.
- Independent latest-main recheck at `c7837e7aae09bf2f3d9b40a77b790d7d6777d799`: candidate **6/6 PASS**, all unaffected injected V1 contracts **9/9 PASS**. The V2 no-op reclassification has its own asserted test.
- Integration harness note: an initial injected-suite attempt missed V16's import-time `AcknowledgedSampler` binding; after patching that alias too, the scoped injected contracts passed. V1's old no-op expectation is intentionally not reused because V2 distinguishes a returned no-op from a failed call.
- `python3 research/doom/acknowledged_scorer_status_59_20261004/audit.py` — **PASS**, all 13 pinned files match; original WSLc 11/11 transcript and baseline characterization remain valid.
- `py_compile` and `git diff --check` — **PASS**.
- Container attempt stopped before execution: the frozen image `sha256:94014a0f…6378` is absent from the current daemon; listing local images fails with containerd content-blob `operation not supported`. No pull, retry, or network fallback was made. The earlier PR's WSLc result remains its own historical evidence; this V2 candidate is not container-validated.

## Scope and immutable lineage

This is an additive candidate on a branch stacked on #7554. No files in the predecessor scorer packet or V1 source/test were changed. The candidate intentionally emits only an untimed partial producer when post-return qualification fails; it does not infer tic advancement from API return alone.
