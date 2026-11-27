# R198 current-main live-control verification — 2026-11-16

## Outcome

The runner emitted `PASS_SCOPED_EXPIRY_DELAYED_OPERATION_BLOCKED`, and the independent ammo-panel oracle observed the preregistered 50→49 effect. A post-run audit found a mismatch against frozen `protocol.query_projection`, so this is **not a full preregistration pass**. The raw runner label is retained; the independent classification is `QUALIFIED_PARTIAL_PROTOCOL_DEVIATION_NO_FULL_PASS`. The current-main source and composed-path test confirm the observed `recovered`/release-true projection is the intended confirmed-recovery branch; the stale expectation is an experiment-condition error, not a demonstrated runtime bug. It is not a claim of overall task success.

- Attempt: `map01-native-expiry-delayed-input-r198-20261116`; dispatches 1, recoveries 1; replay disabled.
- Source: main `86a52662dc2bb690dd670d52ea8d97816aef2a26`, tree `c35b16d1df4f2e7c6b70a09e2ec672043ace5335`; 11 runtime files hash-pinned from that checkout. Worktree was clean before launch.
- Frozen conditions: `conditions.json`, SHA-256 `6be7e6d8aedd045b6b6eb01c0bdb042861274a38e6d98a02165b800dc9031ebc`. Conditions and outcome are unique to R198; no prior attempt was replayed.
- Initial checks: native Windows, display 1920×1080, no existing GZDoom process, custody clear with no pending operation (revision 967), pinned game assets, Python/clock and source hashes all matched.
- Computer Use gate: the unique GZDoom target window and MAP01 HUD were passively observed before input and after recovery; target HWND/root HWND and PID independently matched in both attempt-bound receipts. Pistol was visible; ammo was 50 before and 49 after.

## Recovery and effect evidence

- One LEFTDOWN was accepted; the recorded pre-expiry action lower bound was 4. SHIFT remained across expiry. The delayed SHIFT-UP and second click were excluded; only one dispatch and one recovery occurred.
- Recovery record: source action status `recovered`, `effect_status=unknown`, release confirmed `True`. Separate native release receipts for LEFT and SHIFT returned SendInput count 1, followed by neutral readback. The frozen condition expected source status `unknown` and release confirmation `false`; both fields differ from the observed result. This is the reason full preregistration acceptance is withheld.
- Expiry-to-release receipt: 31 ms against a 1000 ms bound. Integrated late-input horizon: 74 observations across 2 s, max sample gap 32 ms. Independent neutral horizon: VERIFIED across 2 s.
- Dedicated calibrated ammo-panel oracle classified 50 → 49 with a single-click observed effect. This is an observed game effect; **`task_success` remains null** because the runtime completion readback was not attempted and no semantic success criterion was evaluated.
- Broad upper-client pixel-change oracle reported `failure`: 324 / 1003200 pixels (0.03230%), below its strict 5% threshold. It does not override the dedicated ammo-panel result and was not used as the task-effect gate.
- GZDoom closed normally without forced termination. Postflight custody is clear, pending=null, revision 976, and no GZDoom process remained.

## Preserved evidence

- Full trial raw copied to `trial-raw/` (224 files, 11,095,726 bytes); SHA-256 list is in `RAW-MANIFEST.json` (manifest SHA-256 `b8e0db103931fbe3936c89dbc00280e47625035535575561cf0a0584059c3b53`). Independent deviation adjudication: `INDEPENDENT-ADJUDICATION.json` (full frozen-protocol pass=false). Contract source/test crosswalk: `CONTRACT-CROSSWALK.md`.
- Read-only preflight and runner console transcript: `runner-console.log`.
- Preregistration: `PREREGISTRATION.md`.
- Runner code/assets were the pinned R193 candidate packet; its 38 packet file hashes and the current-main runtime hashes are recorded in the frozen conditions. The runner's temporary trial files stayed in the packet's unique R198 directory; no older trial was changed.

## Remaining boundary

This provides a current-main live observation of the expected task effect, but the source-status projection deviation prevents counting R198 as a full preregistered pass. It does **not** measure model/provider token use, cold/warm/invalidation/repair arms, matched correctness and latency across approaches, or total integrated resource cost. Issue #57's matched integrated comparison remains outstanding, so the broader computer-control goal remains active. The corrected independent R199 run is preserved in `../r199/LOCAL_AUDIT_REPORT.md`; it does not rewrite R198. Next, use the confirmed-recovery projection from the audited current-main contract for any new unique attempt, keep `task_success=null` absent a semantic success predicate, and never replay R198. The corrected independent R199 follow-up, with a distinct attempt ID and updated frozen projection, is preserved in `../r199/LOCAL_AUDIT_REPORT.md`; it does not alter R198.
