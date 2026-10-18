# V39 ACK observation dispatch — applicability correction

## H/T/D/C/U

- **H:** The artificial typed-observation-before-accepted-ACK ordering used by the original #8441 helper test is not reachable on the audited V39 V12/V15 session routes: acceptance is synchronously emitted and flushed before the accepted program's worker can produce its active typed observation, and the controller reads one stdout stream in FIFO order.
- **T:** Reconcile the original regression with the current source route. The source-order test checks both V12 and V15 wiring, the synchronous accepted emit before worker start, the synchronous release-wrapper delegation, the locked/flushed session emitter, and the controller's decode/enqueue order. Focused tests were run on WSLc against current main in normal and optimized Python.
- **D:** Remove only the unreachable ACK buffer and its synthetic pre-ACK regression; retain the source-order audit and existing paired-observation invalidation test. Preserve the original #8441 experiment/report and its original outcome unchanged. This successor is separated from unrelated historical archive deletions present on stale PR #8451.
- **C:** A deployment with another session implementation, concurrent output path, or changed scheduling may have different ordering. The AST assertions are source-shape evidence, not live scheduling evidence.
- **U:** No Doom process, GUI/input backend, live executor, formal allocation, physical release, or task outcome was tested. Passing source-order checks do not establish those properties.

## Verification

On current-main source content, `research.doom.test_map01_v39_pair_wait_dispatch` passed 2/2 normally and 2/2 under `python -O`; the changed Python files compiled and scoped `git diff --check` passed in WSLc. GitHub Actions status for the source proposal was unavailable at the time this record was prepared.

## Provenance

- Original synthetic dispatch proposal: [#8441](https://github.com/Unjuno/agent-interface/pull/8441), merged as `ffd4544a4816ded386616e8e614b5a17e6c992ef`.
- Applicability/reversion proposal: [#8451](https://github.com/Unjuno/agent-interface/pull/8451). This mainline successor carries only the runtime/test correction and this addendum; it does not carry #8451's unrelated deletions.
