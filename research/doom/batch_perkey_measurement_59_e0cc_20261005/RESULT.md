# V15 ordered-batch keymap measurement integration

The opt-in V15/per-key route now selects the current owner and ordered release backend. A versioned `keymap-batch-edge-v1` record ties each measured DOWN to its batched UP by owner, intent, key and a non-reused hold identity. V39 projects complete pairs only after the existing V4 and batch publication checks pass.

DOWN adds two keymap queries when measurement is enabled and rechecks focus, cancellation and deadline after the pre-query. UP timestamps existing queries: a shared pre-batch snapshot, a shared post-batch snapshot, and any existing per-key retry sample. No keymap query is inserted between original ordered UPs. Shared snapshot bounds are explicitly labeled and remain correlated. Any unverified key suppresses confirmed brackets for that batch, preserving the release-pending gate. Duplicate DOWN and cleanup invalidate pairable identity. Authority and application consumption remain false.

The default raw owner adds no keymap queries; standalone V12 keeps its archived A01 route with the source mismatch guard. V15 selects a distinct bridge backed by current V4/current raw V12. The new helper is included in the startup source manifest. The V39 backend label distinguishes V12/A01, V15/shared-batch measurement and the two defaults.

## Executed checks

| Run | Result | Meaning |
|---|---|---|
| startup-red-v1 | 2 failed assertions / 5 methods | Old routing rejects the intended current owner and accepts an archived cached owner in the V15 route. |
| owner-red-v1 | 13 errors / 9 methods with subcases | Baseline constructor has no measure_key_edges option; no owner starts. |
| startup-green-v1 / v2 / v3 | 5/5 PASS each | Fresh-process actual startup stops before Session; current/archived/cache selection checks. |
| owner-green-v1 / owner-green-v2 | 9/9 PASS each | Actual owner thread with fake Xlib; normal/repeated/duplicate holds, first/last retry, pre/post failure, persistent loss, subsequent DOWN refusal, cleanup identity, added DOWN query invalidation and disabled query count. |
| composition-green-v1 | 8 errors / 4 methods | Harness used raw arguments in the wrong order and checked a raw stop attribute on a wrapper. Retained unchanged; no result counted. |
| composition-green-v2 | 4/4 PASS | Corrected harness joins current owner, V4, batch publisher and extracted actual V39 projection function. |
| composition-green-v3 | 7/7 PASS | Adds cancellation, expiry and focus changes during batch post-sampling; no ordinary confirmed pair. |
| adjacent-v1 / adjacent-v2 | 8/8 PASS each | Existing cancellation, release retry, failure preservation, V13 terminal and cross-key sample custody regressions. |
| mixed-error-red-v1 | 1/1 FAIL | Audit counterexample: UP delivered before send exception leaves a sibling bracket confirmed. |
| composition-green-v4 | 8/8 PASS | Batch-wide downgrade now triggers on any unconfirmed measurement; neutral cleanup state stays independent. |
| projector-legacy-v1 | 16/16 PASS | Existing A01/legacy identity and CLI tests against exact AST-extracted V39 functions; retained A01 input read, not rerun. |

The separate-agent review found that post-query neutrality could coexist with a send/sync error and leave a sibling measurement confirmed. The counterexample was reproduced before repair, retained, then fixed by downgrading all batch brackets whenever any per-key measurement is unconfirmed. The raw owner, composition, default adjacent and startup suites were rerun for this concrete production repair. Startup v3 additionally verifies the final source-mismatch diagnostic wording. The 16 legacy projector tests are reused because their exercised V39 function and inputs did not change in the raw-owner repair.

Final focused suite total: 46 test methods across five separate processes, including additional subcases. This is not all-repository CI. Eleven changed/new Python files compile and the scoped whitespace check passes. No project lint/typecheck configuration exists at the repository or the two touched source directories; no unrelated full-tree suite was run.

The composition test uses actual measured backend construction with only the ancestor initialization stubbed, then actual raw dispatch, owner thread, V4 validation, batch publisher and the AST-extracted unmodified V39 projection function. It does not run a Session, entire V39 controller loop, model or game. The existing adjacent suite exercises the default V15/V13 paths.

## Custody and boundaries

Source base: parent #8065 6591b5703862c73d375a6646374ad82a26505bcb plus own #8094 guard and own #8103 sample-custody repair; local combined base 935473ee53b760d8be64906cbbfb962643c9474e. All run source manifests resolve to retained content-addressed inert Python snapshots. The intermediate composition-v2 test snapshot was reconstructed by reversing the additive v3 test extension, then matched to its original execution SHA. First results and construction failures remain retained.

The owner test was strengthened before the green run so each DOWN invalidation hook is reached and the fake focus resets between cases; owner-thread termination is checked. The initial red run used the earlier test version and stopped at the unsupported constructor option. These are ordinary regression repairs, not replays of a formal allocation.

Main advanced from 2e1def5886740e347dc6f4ecd4a2f158056a38dc to 0db00a564daff64e47fd6931954ace0f71ab8f2b during this work. Within the checked source closure and canonical documents, the only change is #8104's two-line wheel touch tracking in raw V12. This patch does not alter that wheel block; integration still needs a nonauthor exact-current-tree check. #8065 remains at 6591b570. No main merge or quorum is claimed.

Python 3.12.14, macOS arm64. Owner times are local monotonic readings in fake-device tests (the existing custody suite uses synthetic labels); none establish real latency or timing bounds. No real X server, OS input, live GUI/game/model/container or formal allocation ran. X keymap state does not establish exclusive physical authority, application consumption, task effect, threat response, bounded live recovery or MAP01 completion.

FINAL-v5 merge quorum remains unassigned. A separate agent wrote the owner regression tests and audits retained raw/code; this is separate-agent technical review, not a nonauthor merge vote or completely independent test authorship.

Separate-agent retained-raw audit v1 passed 19 readback checks and its code review found the mixed-error sibling leak. Follow-up audit v2 failed because its source allowlist contained only base/current versions and omitted retained intermediate source blobs; the failed script/result are preserved. Corrected v3 verifies content-addressed bytes and passes 14 repair/readback checks without rerunning the candidate. This audit correction does not change the test thresholds or raw results.
