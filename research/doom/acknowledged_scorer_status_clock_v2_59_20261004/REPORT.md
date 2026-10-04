# Post-return clock failure: acknowledged-update successor

## H/T/D/C/U

- **H**: The #7554 `AcknowledgedSampler` loses a returned update if its follow-up clock fails. The same hole exists one layer earlier: V16 `ObservedGameProxy.advance_action()` calls the inner game, then reads a return clock before exposing the API return to the sampler. Update return, timing/tic qualification, and scorer availability are separate facts.
- **T**: Preserve exact #7554 head (`9e33a99e495b148f9dbfa90fef16413859b271de`). Reproduce failures in both the raw scorer path and V16 proxy path. Add an opt-in V17 wrapper that latches inner-call return before fallible metadata reads, composes the V2 sampler, records the selected sources, and restores V16 globals on unwind. Keep no-sample/no-retry, no-fabricated metadata, and predecessor packet integrity; recheck against latest main (`c7837e7aae09bf2f3d9b40a77b790d7d6777d799`).
- **D**: TDD red on both raw scorer and the V16 proxy: after the inner call returned and fake tic advanced 7→10, a return-clock `OSError` yielded `UPDATE_UNAVAILABLE` and no producer; the proxy regression confirmed one inner call occurred. V17 now records a partial `UPDATE_RETURNED_UNTIMED` producer without return time/tic-after, skips sampling, latches failure, and does not retry. Candidate+V17 tests pass 9/9 on both #7554 source and latest main. V2-injected unaffected existing contracts pass 10/10 on #7554 source and 9/9 on latest main; the old no-op assertion is intentionally replaced by a dedicated V2 assertion (`UPDATE_RETURNED` + `UPDATE_VALIDATION_FAILED`). Unmodified V1 suites pass 11/11 and 10/10. The #7554 packet audit passes with 13 manifest files.
- **C**: Native Python fake-game/source construction. V17 binds both sampler and observed proxy only during the wrapped V16 main call, restores both on failure, and adds V17/V2 hashes to existing `sources.json`. No actual V16 session, engine acceptance, scorer efficacy, useful feedback, physical release, recovery, or gameplay claim.
- **U**: Run this V17+V2 composition in the hash-pinned container once the cached image/runtime is available, then independently audit and review. Live qualification remains gated by the current roadmap's exclusive allocation and threat-exposure requirements.

## Executed checks

- TDD red on the exact #7554 working-tree source: targeted test failed because `UPDATE_UNAVAILABLE != UPDATE_RETURNED` after one successful API return.
- TDD green: `PYTHONPATH=research/doom:research/doom/acknowledged_scorer_status_clock_v2_59_20261004 python3 -m unittest -v test_session_map01_v17 test_acknowledged_scorer_clock_v2` — **9/9 PASS**.
- Existing V1 suite: **11/11 PASS** on #7554 source; **10/10 PASS** on latest main.
- Independent latest-main recheck at `c7837e7aae09bf2f3d9b40a77b790d7d6777d799`: V17+candidate **9/9 PASS**, all unaffected injected V1 contracts **9/9 PASS**, current-main V1 suite **10/10 PASS**. The V2 no-op reclassification has its own asserted test.
- TDD red for V16 proxy path: third injected clock call (V2 start, proxy start, then proxy return timestamp) raised after inner update. The first harness setup failed before reaching the inner call; after targeting the third call, the regression reproduced the lost ACK. A separate initial integration-suite harness missed V16's import-time sampler alias; both sampler and proxy aliases are now patched/restored by V17 and explicitly tested.
- `python3 research/doom/acknowledged_scorer_status_59_20261004/audit.py` — **PASS**, all 13 pinned files match; original WSLc 11/11 transcript and baseline characterization remain valid.
- `py_compile` and `git diff --check` — **PASS**.
- Container attempt stopped before execution: the frozen image `sha256:94014a0f…6378` is absent from the current daemon; listing local images fails with containerd content-blob `operation not supported`. No pull, retry, or network fallback was made. The earlier PR's WSLc result remains its own historical evidence; this V2 candidate is not container-validated.

## Scope and immutable lineage

This is an additive candidate on a branch stacked on #7554. No files in the predecessor scorer packet or V1 source/test were changed. The candidate intentionally emits only an untimed partial producer when post-return qualification fails; it does not infer tic advancement from API return alone.
