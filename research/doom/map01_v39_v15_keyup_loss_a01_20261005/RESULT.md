# Result — current V39/V15 lost-KeyRelease composition probe

**Disposition: `FAIL_BATCH_PHYSICAL_RELEASE_NOT_ESTABLISHED`; per-program cleanup `UNRESOLVED`.** A03 candidate and independent audit ran once each against current-main source `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`; the auditor passed 16/16 checks. The paired normal fake-X case left no key down after the batch. In the injected-loss case, fake keycode 38 remained down after the release batch, but the emitted row still had `owner_transition_verified=true`, `owner_thread_keyup_verified=true`, `ordinary_release_candidate=true`, `release_batch_complete=true`, and `owned_keycodes_after_batch=[]`. It also correctly retained `physical_verification_authoritative=false` and `grants_input_authority=false`. A03 called owner close after the direct backend batch; it did not execute V13's production per-program cleanup.

The result isolates a gap in this selected composition slice: its ordinary batch receipt verifies owner bookkeeping and XSync completion, not actual server key state. A dropped release can therefore survive the batch while its row looks ordinary. A03's later owner-close diagnostic found the still-down key, but that is not evidence about the per-program executor cleanup. A04 attempted that production-path check against current-main `402c7d1b5147b2a905098f082233db60a47d68db`; the constructor STOP occurred before either case, so per-program cleanup remains unresolved. This supports keeping the per-key physical-state and live release/reaction gates open. It does not establish a real X server event, application consumption, harmful game effect, useful feedback, recovery efficacy, latency bound, threat response, or MAP01 progress.

## Frozen identities and preserved construction history

- A01: constructor mismatch STOP; no case started. See `FREEZE.json` and `results/candidate-a01/STOP.json`.
- A02: finalizer wrapper-field STOP after the normal fake-X case; the injected-loss case did not start. See `FREEZE_A02.json` and `results/candidate-a02/STOP.json`.
- A03: paired candidate raw at `results/candidate-a03/candidate.json`; independent audit at `results/audit-a03/audit.json`; frozen candidate/auditor/source hashes in `FREEZE_A03.json`.
- A04: production per-program cleanup attempt froze `402c7d1b5147b2a905098f082233db60a47d68db`; candidate STOP at `results/candidate-a04/STOP.json`; see `RESULT_A04.md` and `FREEZE_A04.json`. Neither paired case started; no audit was run.
- Exact WSLc commands, exit codes, and host resource warnings are in `RUN_COMMANDS.md`.

After the candidate run, main advanced from the frozen `018934cdf45fcabffcc4efe25b5c7b3d59bd459f` to `402c7d1b5147b2a905098f082233db60a47d68db`. The tracked V15 launcher, release-batch backend, V2 telemetry, V4/V3 wrappers, V12/V10 owners, V3 executor, and lease files in `FREEZE_A03.json` remain byte-identical at the newer main tip. This is a posthoc source identity comparison, not a rerun on the newer tip.

## Scope and next decision

The real V15 release-batch backend, V2 telemetry layer, and V4→V3→current V12 owner sources were loaded. Only the controller's base action loop was replaced with a tiny test double to submit one F8 down/up list through the production `execute`/`raw` seams; the V15 launcher, ViZDoom, real X11, GUI, model, game, and physical input did not run. A01 and A02 construction failures are preserved and were not rerun. The private #59 live-game allocation remains unassigned. This result motivates requiring a non-ordinary batch/cleanup outcome when an XTest release is dropped; it cannot substitute for a newly frozen live threat exposure.
