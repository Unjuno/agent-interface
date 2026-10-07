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

## Append-only follow-up: frozen A02 formal T0 run

Freeze readback matched GitHub branch content and the five frozen source SHA-256 values. Main remained `fc595c0693750e4214d8f02f393b71db64db8894`; freeze commit `847332de8b1ce3a7044baf08792384ba5a1e585d` was the execution checkout; both formal outputs were absent before the candidate call.

- Candidate CLI, exactly once: exit 0; stdout/stderr empty; produced 50 rows (48 matched, 2 position controls), 507279 bytes, SHA-256 `fddae0822660244e03dfc9aca8a9807839d22081e2faf3dc72d770dcf4276280`.
- Independent auditor CLI, exactly once: exit 0; PASS, 48 matched, 2 position rows, zero errors; stdout `{"errors": [], "matched_rows": 48, "position_rows": 2, "result": "PASS"}`; stderr empty; output 66 bytes, SHA-256 `6727564a6b867e659e187f88e17acf9521f07d5eab9a720a2a68c0229bc7ffa1`.
- Scoped disposition: `PASS_FIXTURE_METHOD_SCOPED`. No retries, model calls, construction tests, imports, or package tests followed the candidate invocation. Only read-only integrity checks followed.

The raw candidate JSON, auditor JSON, exact run record, and scoped interpretation are in `results/formal/`. This result concerns only the deterministic synthetic fixture method. It is not model-facing proactive-interference evidence and does not establish tokenizer/attention equivalence, GUI/task effect, human outcome, latency, safety, deployment, or generalization. T1/model study remains unauthorized. No container was needed for the explicitly authorized host-only no-model fixture run; no isolation claim is made.

## Append-only follow-up: serialized-history gate and repository checks

The independent auditor and its eight-mutation construction suite were strengthened to validate the actual fixed-slot episode bytes by arm/depth, not merely metadata. The common-byte mutation now updates the serialized reconstruction consistently so the auditor must catch cross-arm identity drift; the history mutation removes an actual depth-4 serialized episode while retaining lineage metadata, so the auditor must catch the missing record itself.

Latest construction run after these changes: `python3 research/analysis/proactive_interference_5947_t0_a02_20261008/construction_runner.py` — 7/7 passed; `git diff --check` passed. Exact current local SHA-256: candidate `336b0c9f12da7527f2f78e4cd75307532ea307ede73a452b58426ee3a80f27dc`; auditor `742068758eab3e4ca2f47cc18e491eeb073dee7ca16737d0a2ac0e99af5a0c6b`; test contract `cab9111cc41335142298e8fa41ba14cd82e53c7bdac6b301d1674f57d6f691e3`; construction runner `d05c207cd585928f12a6da0823e2b618217d37d7db323e38f768969ba197fc40`. GitHub MCP readbacks for candidate, auditor, tests and runner exactly matched their local UTF-8 content.

Repository checks: analysis index reports 768 retained result/failure directories indexed; analysis-index tests 22/22 passed. Workspace index reports 160 top-level research directories reachable; workspace-index test 1/1 passed (run from the `research/` directory as required by its import layout). Initial workspace-index attempts in the sparse checkout stopped because required index inputs were outside the sparse set; those inputs were added to this isolated A02 worktree's local sparse specification only. The repository source/index files were not altered for that setup.

Protocol written to `PROTOCOL.md`. Formal candidate calls remain 0, formal auditor calls remain 0, model calls remain 0, and no result output exists. The exact freeze has not yet been written.
