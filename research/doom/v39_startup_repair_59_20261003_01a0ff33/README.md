# v39 startup ownership repair — #59

Current v39 acquires its planner client, session child and stdout reader before validating the fixture and initial observation. A missing fixture raises while those resources remain live. This runtime patch attempts cleanup on any failure from client initialization through initial observation, records incomplete cleanup, and re-raises the original failure. Acquired-session stdin EOF is followed by owned-PID wait/terminate/kill stages (one second each); readers are joined and stderr is retained with an explicit 64 KiB cap. Failed client close keeps the original exit callback registered. Normal control and successful finish bytes are unchanged.

Original diagnosis: [#6933](https://github.com/Unjuno/agent-interface/pull/6933), immutable head `f68715fba950d2e2c99c28ed3e30012b28602452`, actual worker e0cc. Original macOS evidence belongs to its author and is not replayed or pooled here. Own prospective assignment: [#59 comment5965936454](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5965936454); the original author acknowledged separation in [5966004735](https://github.com/Unjuno/agent-interface/pull/6933#issuecomment-5966004735).

## Actual checks and preserved first outcomes

Windows build26300, CPython3.11.9; native private subprocesses, pipes, threads and EOF are real. Client/planner/game/import boundaries are explicit inert fakes; zero decision iterations. Current source has eight ordinary methods, 8/8 PASS in normal mode and 8/8 PASS with `-O`; each final phase starts five private children sequentially. Tests cover missing fixture, noncooperative owned session, normal finish, initialization failure, Popen failure, client-close failure, stdout-reader start failure, and stderr overflow. The controlled noncooperative case meets its <4s assertion; this is not a whole-runtime hard bound.

| Retained phase | Actual runner exit | Child invocations |
|---|---:|---:|
| first-red | 1 | 1 |
| green-normal | 1 | 3 |
| green-normal-v2 | 0 | 3 |
| green-final-normal | 0 | 5 |
| green-final-optimized | 0 | 5 |
| release-normal | 0 | 5 |
| release-optimized | 0 | 5 |

All 27 child invocations are ordinary repair checks, not independent scientific trials. Original PLAN proposed four total and the claim used <=5 sequential wording; actual repeated repair phases exceed that prospective total, explicitly corrected in [CORRECTIONS.json](CORRECTIONS.json). Every retained case has external teardown records. Before external fixture teardown, final repaired cases already show acquired child/reader closure; the original RED does not.

The first byte editor failed on mixed LF/CRLF source, leaving production unchanged. A dependent phase labelled green-normal was mistakenly run on baseline and failed; its label, exit1, logs and source pins are preserved, not declared green. Later source corrections were checked before tests. First reader and result remain; v2 adds literal error/release checks and rejects eight copied-record mutations. Reconstructed intermediate controller/test copies match contemporaneous receipt hashes but were reconstructed later, as [SOURCE_INVARIANTS.json](SOURCE_INVARIANTS.json) states.

## Evidence custody and review

[PUBLICATION.json](PUBLICATION.json) binds every retained original to its public derivative and identifies path-token projection. Original receipt log hashes describe original bytes; final normal/-O logs are unchanged. [MANIFEST.json](MANIFEST.json) binds all package files except itself. Final source snapshots duplicate the actual runtime/test and two unchanged data inputs exactly. Baseline controller bytes and mixed EOF newline are preserved exactly; archived helpers use `.py.txt` and are excluded from automatic Python discovery. The active regression module is intentionally executable and uses only standard-library fixtures with actual owned children. No workflow or discovery rule is added.

Saved-only reader commands, without importing subject/tests or starting children:

```
python -B audit_saved_v2.py.txt <this-package-directory> <new-output-path>
```

This reruns a retained-data reader, not a native producer. Private originals retain their full host paths; public logs/receipts substitute owned local paths with tokens, and no authentication/session transcripts are included. Final source/test pins are in [RESULT.json](RESULT.json). Acceptance votes, head/diff digest and application records belong outside this source tree to avoid self-reference.

## Limits and approval scope

The patch covers resources acquired after a successful client constructor and before the first observation. A partially failing constructor, later actions/futures, descendants, stream flush blocking, game teardown, actual app-server/client journal-lock bounds, input release and useful task feedback remain outside this check. Client close is attempted with timeout1 but its implementation can block on journal/reader details; this code does not establish an overall deadline. Parent PID was not independently recorded: ownership linkage is source-qualified by the fixture Popen, child PID and trace, not a raw parent-PID attestation. Termination is not physical key release. No GUI, actual game/model, GPU, container/WSLc, or consumed formal allocation is executed by this evidence. #59/R134/#57 remain open.

Content review must preserve these limits, original failures and source/raw identities. Reuse on a later main requires unchanged head/important dependency/test conditions, inspection of intervening changes, and a fresh actual-base/head/tree application record with a nonauthor linkage. Two assigned genuine nonauthor content approvals and actual required GitHub/ownership/conditional-forward gates are still required; publication does not imply application.
