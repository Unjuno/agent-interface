# A02 construction-test status — attempt 1

This is an append-only construction record. No formal candidate/auditor execution or freeze occurred.

The test-first contract exposed multiple design defects before formal allocation:

1. Current cue byte offset was mistakenly computed after the cue and was identical for every condition/arm; the position control offset was incorrectly derived from prefixes whose markers were only in the history slot.
2. Fixed padding was appended after variable history. That held total bytes but did not keep common suffix bytes exact; history slots could exceed the pad at depth 8.
3. The raw JSON interface cannot encode Python bytes directly, while the test mutation helper is undefined in the test module.
4. Baseline-change records need full baseline source/value equality checked from serialized identity, not merely source-id cross-check.

This record makes no claims about candidate/auditor PASS. Next construction patch will encode all byte fields as UTF-8/base64-decodable hex text in JSON, use a fixed exact prefix and suffix, isolate history in a fixed-capacity slot, put a unique current-cue marker in the shared prefix, define mutations in the test module, and require the independent auditor to verify exact baseline object/source bytes, complete group row identities, expected row IDs/arms/depths, and the separate position-control-only offset change. Rerun construction tests only; freeze remains deferred until all controls pass.

## Append-only follow-up: A02 construction tests on dedicated checkout

Environment: macOS arm64, Python 3.14.5, standard library only; checkout at GitHub A02 branch tip commit `3fba9f78abab1e1ad21713dc7326f716a4c83017`, with later local source changes exactly matching the subsequently published GitHub file readbacks. No container, model, network call from the test process, GUI, user data, or application was used. This is allowed host-only construction work under Issue #8341 and makes no isolation claim.

- Attempt 2: `python3 research/analysis/proactive_interference_5947_t0_a02_20261008/construction_runner.py` — 6 tests, 1 failure. Seven other assertions passed; the lineage mutation selected a depth-0 row whose lineage was already empty, so the auditor accepted a non-effective mutation. The test selector was corrected to use a depth-1 row.
- Attempt 3: same runner — 7 tests, 13 errors/1 failure caused by a construction edit that removed the global PREFIX constant but left three stale references; the CLI candidate therefore exited 1 with NameError before writing output. This was a source-construction failure, not a formal attempt. References were corrected before further tests.
- Attempt 4: same runner — 7/7 passed. This covers complete 50-row/48-matched/2-position corpus shape, condition×depth×arm coverage, matched baseline value/source bytes and current evidence identity, exact prefix/history-slot/suffix reconstruction and equal byte budget, explicit unsupported UNKNOWN, the position-only cue-offset pair, independent auditor PASS, all eight corruption mutations both through the independent function and CLI, CLI pass/fail behavior, and refusal to overwrite occupied output paths. `git diff --check` also passed.
- Formal candidate calls: 0. Formal auditor calls: 0. Model calls: 0. Freeze has not yet been published. Retries of a formal allocation: 0.

Local SHA-256 after Attempt 4: candidate.py `336b0c9f12da7527f2f78e4cd75307532ea307ede73a452b58426ee3a80f27dc`; auditor.py `69b3faec0b52648fe584318e3d2032c771d9a10281ac47d0296952ce6c69fc41`. The test file was extended afterward to invoke all eight CLI mutation cases and to mutate baseline bytes together with source ID; the full 7/7 construction suite was rerun after that extension. Current exact hashes will be recorded in the freeze.

The suite only qualifies the finite authored fixture method. A PASS does not establish model behavior, proactive interference, tokenization/attention equivalence, task effect, or T1 authorization.
