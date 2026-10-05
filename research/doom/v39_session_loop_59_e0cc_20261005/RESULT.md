# V39 to actual child Session construction

**Result: PASS for the exercised synthetic integration; expected fail-closed STOP for persistent synthetic KeyUp loss. Live task effect remains untested.**

The actual V39 main loop now reaches the actual V15/V12 Session main in a separate Python process, through its real JSON pipe, typed Executor, selected measured backend, transition wrapper and raw owner thread. The controller compiles semantic commands, admits and monitors them, cancels cover, verifies release, reconciles typed/full frames and builds its report. External Xlib, game, capture, HUD recognition and model transport are synthetic. No live allocation or consumed formal run was used.

The source composition carries the observation identity and frame barrier from #8031 into #8094 after reconciling main `38fe303fec59cde15f708483cae00bf617f3bdd0`. It retains main's completed/expired verified-neutral terminal handling and #8094's pending/no-active-cover renewal handling. The initial-cover invalidation branch also waits for the matching full image before continuing. Source-selection diagnostics use POSIX relative paths for cross-platform comparisons; manifest lookup retains the producer's native path convention. Windows execution was not performed.

| Construction | Result | What it establishes |
|---|---|---|
| child-01 | Preserved harness failure | A socket type replacement prevented import before owner startup. |
| child-02 | PASS | Real child Session accepted a bounded two-key command, emitted verified release and score, and exited 0. |
| full-01 | Preserved harness failure | The parent subprocess shim lacked the PIPE constant; no child started. |
| full-02, full-03 | PASS before identity composition | Normal and hard-change real-parent/real-child boundary, with single-key primary actions. |
| full-04 | PASS | Two normal three-key primary programs; 6 ordinary measured edge pairs; 2 canceled-cover receipts remain incomplete. |
| full-05 | PASS | Hard health change during pending inference interrupts turn 2 before its late eligible answer. That answer is discarded, no plan-1 is submitted, and the next prompt/source frame uses health 60. |
| full-06 | PASS | UNKNOWN health during pending inference has the same rejection behavior; a real passive source-refresh program obtains recovered health 60 before the next prompt. |
| full-07 | Expected STOP | Persistent synthetic KeyUp loss produces an unverified failed terminal. No plan-1 or third model turn follows. Child exits 1; fake key 24 stays down; cleanup remains explicitly incomplete. All five fake display connections close. |

The three passing final scenarios exit 0, leave no fake keys down, and close all five fake display connections. Every primary three-key release shares one measured batch snapshot. Real controller projection pairs ordinary edges and refuses to promote canceled cover into an ordinary release certificate. `audit_runs.py.txt` uses independent raw event/image checks; `raw-audit-v1.json` records 219/219 passing checks across full-04 through full-07, including the expected negative result. The audit does not import the production projector.

The scoped suites cover 75 distinct test methods. The first batch-composition invocation failed eight methods before execution because the runner placed `doom` before `live_control` in PYTHONPATH and resolved the wrong bare `session_v7`. Only that runner path order was corrected; the same eight tests then passed. All original failure logs remain under `scoped-tests-01`. The other nine suites passed on their first invocation. Those include 17 controller tests, 6 observable-guard tests, owner measurement/custody, source selection, wheel cleanup and adjacent dual-signal checks.

Three additional executable unit cases isolate the actual initial-cover branch and production release/frame helpers. The pre-barrier baseline fails both matching-frame/absent-frame cases while retaining the release guard; the composed candidate passes 3/3. After removing private hardcoded test paths, all 3 cases also pass against the exact production controller bytes (`initial-barrier-production/`). Together, the retained suites cover **78 passing distinct test methods**. Wrong-binding and stale-capture rows are rejected; an absent matching frame times out; unverified release prevents the frame wait. Earlier unit-harness construction failures remain retained in `identity-composition/receipts/`.

The source-composition coauthor spot-checked full-04 through full-07 raw. The corrected review is `identity-composition/initial-cover-review-v2.md`; it supersedes the original review's incorrect ordering sentence, which is retained as v1. Actual order is interrupt, cover terminal, late eligible answer, then next model for full-05/06; full-07 stops after its failed terminal and late answer. This technical raw check is not a nonauthor content-quorum vote.

Source/test whitespace checks pass. The all-staged whitespace check exits 2 because the inert archive preserves original conflict markers, patch context whitespace, one unfinished historical test line and original source-blob EOF spacing. Those exact historical bytes are retained; this is not a clean whole-archive whitespace result (`publication-checks/`).

## Source and evidence custody

`source-index-manifest.json` records the original exported index objects. `source-closure.json` and `source-blobs/` retain the exact distinct Python bytes actually imported by the parent/child runs. Per-run loaded-source manifests remain beside each raw run. Harness versions were copied before each invocation. `applied-composition.json`, `composition.patch`, and `test-composition.json` identify the source/test composition. Production V39 retains the owned branch's CRLF convention; the executed export used LF. `line-ending-equivalence.json` verifies normalized byte equality and AST equality including locations, and records both SHA-256 values. These are not byte-identical files.

Later main `82b6eaa0d96f233a2f3e7acc744e3396d504cf4c` was read through Git; all 69 loaded-runtime, required non-Python and canonical-document paths were unchanged from the tested main base (`later-main-closure-delta.json`). This is dependency-delta evidence, not authorization to update main.

## Limits and integration decision

Retain the implementation as a review candidate in owned draft #8094. No nonauthor content quorum or exact-tree main-application approval is claimed. This worker has not updated main.

The passing actual-child cases do not delay full-frame transport adversarially: their frames arrive naturally before replanning. They establish the real process boundary, not every event interleaving. Focused unit regressions separately address identity/barrier interleavings. The synthetic third model answer uses `state=dead` only to terminate the scripted controller path; the independent fake game's score remains alive/unfinished and no success or death inference is drawn from that answer. The preserved production report has a fixed claim mentioning real MAP01 and `game_continued_during_model_calls=true`; those strings are generated by production code and are **not** evidence of a real game or live progress in this harness.

No real X-server behavior, physical input, model inference/quality, damage/kill/task benefit, live recovery latency, resource improvement or MAP01 completion was measured. The separate live lane remains unassigned. The unresolved goal is still correct live task effect and finite recovery with lower waiting/model/resource cost.

GitHub API PR readback encountered a primary rate-limit HTTP 403 at 2026-10-05 09:55:24 UTC (`github-rate-limit.json`), and remained limited at 10:02:56 UTC (`github-rate-limit-readback.json`). No repeated write request or alternate principal was used. Publication state is recorded separately after commit/push; this report is not a publication receipt.
