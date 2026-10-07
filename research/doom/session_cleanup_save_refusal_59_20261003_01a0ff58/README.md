# v12 cleanup after evidence-save refusal

Scientific parent: [#59](https://github.com/Unjuno/agent-interface/issues/59).
Prospective ordinary CPU scope: [claim5965906951](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5965906951).
Source/test commit after local checks: `629b6e3b155b80a78fe69a90d300fdeab21fb7e2`; historical main reference `9c26e204c0475bee30919e3d0e6681f393078ef1`.

## Result and bounds

Unmodified actual `session_map01_v12.main()` with actual idle Executor v12 reaches EOF under explicit VD/game/IWAD/X11/backend/input-owner/HUD/screen fakes. A real directory occupying owner-events.json produces native Windows PermissionError at the actual write. Backend close is called; game/session close are skipped and an actual private bounded inert Python child remains alive at main return. The wrapper then closes its stdin and reaps exit0. Normal control closes all and reaps exit0 inside main.

The runtime proposal nests finally blocks in the original executor/backend/game/session order, so earlier cleanup/save exceptions cannot skip later independent close calls. Errors remain raised, including their exception contexts. Failed config preservation or failed session close preserves its temporary directory. This attempts cleanup; it supplies no timeout for a noncooperative close and does not prove real physical release.

Three ordinary main phases, each with normal and filesystem-refusal controls, retain six distinct owned-child invocations. Both repaired candidates reap their child at main return while the actual PermissionError remains visible. All six final receipts/EOF bytes report exit0; no self-cap or kill was observed. Final runtime/test pass9 regressions covering normal/partial setup, actual owner-save/config-copy errors, close errors, exception context and directory preservation.

## H/T/D/C/U

H: actual v12 sequential teardown loses later owned cleanup after an owner-record save refusal.
T/D were recorded before each ordinary capture in BEFORE.json and the claim: normal no-error closes/reaps; original fault exposes OSError, skipped later calls and live owned child; repair keeps the same error and closes/reaps. These are ordinary rerunnable construction/regression checks, not a formal allocation or replay of historical experiments.
C: engine/X11/backend boundaries are explicit fakes; real main control flow, Executor imports, pathlib write, stdin EOF and inert child process are exercised. Twenty literal v12 provenance files plus executor_v3 (21 exact historical Git exports) are retained; eight actual Executor/lease imported-module paths are recorded. No executed submit/cancel/controller task.
U: only Windows/CPython3.12.14, idle Executor, EOF and cooperative close. No live game, model, input-owner, per-key release, scorer/task correctness, timeout/recovery bound or performance comparison. Calling game.close through another proxy may itself fail; session close is still attempted. Real v13 scorer/VD/backend adoption requires separate applicable validation. Historical formal producers were never invoked.

## First failures and repairs

- first-unit-red-01:9 methods,5 assertion failures/1 error. Its config-copy fixture falsely assumed copy2 rejects a destination directory. Original test/source/raw/receipt remain.
- first-unit-red-02-fixture-repair: actual resolved destination-file refusal; unchanged runtime,9 methods,5 assertion failures/1 error. This diagnoses six teardown paths; the multiple-error case stops at the earlier write as expected on old source.
- first-unit-green-01:9 pass. That first candidate removed config source after failed preservation; code inspection caught this before publication. It and both actual main-case receipts remain.
- unit-green-02-config-preservation:9 pass with tightened config-source retention; final runtime/test snapshots retained. repaired-main-02-config-preservation checks the final exact code.
- First post-result record reader assumes POSIX provenance separators and fails KeyError on actual Windows backslash key. Its source remains, as does the original tool trace; no fabricated standalone first-error raw file is claimed. Separate reader v2 normalizes only keys, rejects duplicate normalized keys, and reconciles all21 original exports,6 actual-main cases and4 unit phases. This author reader is post-result custody/behavior reconciliation, not independent scientific validation.

## Custody and nonexecution

All original private files remain unchanged. CUSTODY.json maps each original/public SHA256 and bytes. Only local-home prefix spellings are projected to LOCAL_HOME; text/log newline bytes are preserved, and JSON projections are decoded/read back. Manifest covers every archive file except itself; archived executable sources/fake PNG/IWAD are .txt. No producer/auditor/default workflow or import is added. The only executable new test outside this archive is the nine-method stdlib regression for actual main's AST finally body. No global index or workflow is changed. Archive-local -text prevents Git newline normalization.

Content quorum/current-base nonauthor application/effective GitHub rules/sole expected-old forward send remain separate. No main write or shared GUI/GPU/VM/apply lock. Peer v39 startup and scorer ownership continue.
