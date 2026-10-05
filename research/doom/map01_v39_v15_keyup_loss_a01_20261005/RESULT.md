# Result — current V39/V15 lost-KeyRelease composition probe

**Disposition: `FAIL_BATCH_PHYSICAL_RELEASE_NOT_ESTABLISHED`.** A03 candidate and independent audit ran once each against current-main source `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`; the auditor passed 16/16 checks. The paired normal fake-X case left no key down after the batch and passed terminal cleanup. In the injected-loss case, fake keycode 38 remained down after the release batch, but the emitted row still had `owner_transition_verified=true`, `owner_thread_keyup_verified=true`, `ordinary_release_candidate=true`, `release_batch_complete=true`, and `owned_keycodes_after_batch=[]`. It also correctly retained `physical_verification_authoritative=false` and `grants_input_authority=false`. Terminal `close` later sampled the touched key and failed closed with `keys_down=[38]`; it did not recover the key.

The result isolates a timing/semantic gap in this selected composition slice: its ordinary batch receipt verifies owner bookkeeping and XSync completion, not actual server key state. A dropped release can therefore survive the batch while its row looks ordinary; detection occurs only at terminal cleanup. This supports keeping the per-key physical-state and live release/reaction gates open. It does not establish an OS keyboard state, a real X server event, application consumption, harmful game effect, useful feedback, recovery efficacy, latency bound, threat response, or MAP01 progress.

## Frozen identities and preserved construction history

- A01: constructor mismatch STOP; no case started. See `FREEZE.json` and `results/candidate-a01/STOP.json`.
- A02: finalizer wrapper-field STOP after the normal fake-X case; the injected-loss case did not start. See `FREEZE_A02.json` and `results/candidate-a02/STOP.json`.
- A03: paired candidate raw at `results/candidate-a03/candidate.json`; independent audit at `results/audit-a03/audit.json`; frozen candidate/auditor/source hashes in `FREEZE_A03.json`.
- Exact WSLc commands, exit codes, and host resource warnings are in `RUN_COMMANDS.md`.

After the candidate run, main advanced from the frozen `018934cdf45fcabffcc4efe25b5c7b3d59bd459f` to `402c7d1b5147b2a905098f082233db60a47d68db`. The tracked V15 launcher, release-batch backend, V2 telemetry, V4/V3 wrappers, V12/V10 owners, V3 executor, and lease files in `FREEZE_A03.json` remain byte-identical at the newer main tip. This is a posthoc source identity comparison, not a rerun on the newer tip.

## Scope and next decision

The real V15 release-batch backend, V2 telemetry layer, and V4→V3→current V12 owner sources were loaded. Only the controller's base action loop was replaced with a tiny test double to submit one F8 down/up list through the production `execute`/`raw` seams; the V15 launcher, ViZDoom, real X11, GUI, model, game, and physical input did not run. A01 and A02 construction failures are preserved and were not rerun. The private #59 live-game allocation remains unassigned. This result motivates requiring a non-ordinary batch/cleanup outcome when an XTest release is dropped; it cannot substitute for a newly frozen live threat exposure.
