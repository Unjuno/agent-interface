# PR #7599 independent raw-sample reconstruction (T1, 2026-10-04)

## H / T / D / C / U

**H:** The saved post-result summary for construction03 can be independently reconstructed from the immutable scorer last-action rows and associated runtime event receipts, while preserving its protocol STOP and not upgrading sampled evidence into useful gameplay.

**T:** On current main `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012`, verify all 89 manifested package members and 1,957 source-preparation Git blob pins against their exact source commit. Reconstruct the 717 action-sampler rows, the sole TURN_LEFT vector interval and neutral neighbors, cross-check the owner XTest/XSync release receipt ordering, and independently reconcile 715 separate progress samples with client updates. Add mutations for a wrong action channel and a reordered key-up receipt.

**D:** `PASS_SAMPLED_GAME_ACTION_STATE_SCOPED` only if raw rows reproduce the retained counts/ticks and ordered release receipt; retain `STOP_PROTOCOL_COMPLETION` if the post-action protocol lacks normal finish and requires external rescue. Useful task effect, exact engine transition onset, and recovery benefit remain unproven.

**C:** Sampling cadence can miss transition edges (the active sample sequence skips tic 1378). The scorer observes game state but does not authorize the controller; owner XSync and an empty owned-key sample are not physical-use or task-effect proof.

**U:** Posthoc CPU-only audit of merged immutable evidence. No game, GUI, model/provider, OS input, container, allocation, or replay was run.

## Reconstructed result

- Manifest: 89/89 members match byte size and SHA-256; `FILES.json` is the sole intentionally unmanifested member.
- Provenance: all 1,957 declared Git blob pins resolve in source commit `4c2fe6cbd4218306bcb203cf04258b0f9a322213`; all 20 copied source files match their pinned SHA-256.
- Action samples: 717/717 are authority-free and tic-coherent. Exactly eight samples show only `TURN_LEFT=1.0`, at tics 1375–1377 and 1379–1383; the sample before is neutral at tic 1374 and the first sample after is neutral at tic 1384.
- The identity-bound `Left` owner key-up/XSync receipt is nested inside the caller bracket after the last active sample and before the owner empty-key sample; the first later neutral scorer sample follows that sequence. The receipt explicitly says physical verification is not authoritative.
- Separate progress ledger: 715 rows link to 715 client updates; every row reports zero death/kill, no map exit and no episode completion.
- Terminal protocol evidence remains failed/incomplete: the later unsupported coast probe times out, its direct child is killed (`-9`), the reader remains alive, and external rescue was used. No normal final score/finish is present.

## Reproduction

From repository root:

```sh
python3 -m unittest research.doom.game_action_sampling_59_independent_audit_t1_20261004.test_audit_raw_samples -v
python3 research/doom/game_action_sampling_59_independent_audit_t1_20261004/audit_raw_samples.py
```

`RESULT.json` is the auditor's exact stdout object. `SHA256SUMS` covers the additive report, auditor, tests and result. The predecessor `SAVED_ACTION_AUDIT.json`, raw logs, and protocol STOPs are read-only and unchanged.
