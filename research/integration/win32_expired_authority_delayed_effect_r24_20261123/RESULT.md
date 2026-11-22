# R24 — delayed application effect after authority expiry

**Disposition: bounded integration failure observed; orphan recovery succeeded.** This is one live Win32 fixture trial against current main, not a MAP01, MAP-wide reliability, or efficiency result.

## Frozen conditions

- Source main: `490d7bcb4d84927116112e5ff348cdeadfc489d6`; runtime and task-ledger trees matched that commit.
- Run: `159fa184854a4e8db5e5fb97a9748fb5`; frozen conditions are in [`conditions.json`](conditions.json).
- One visible fixture (`Agent Interface Win32 Fixture R24`), exact HWND `26411224` / PID `43388`; public observe, one `focus + A + release_all` dispatch, exact results lookup, observe, close. No provider/model, retry, or replay.
- Action lease: 2,000 ms. Fixture effect delay: 6,000 ms. Recovery neutral horizon: 2,000 ms, maximum allowed sample gap 100 ms.
- Preflight against the pinned main source passed 60 tests normally and 60 under `-O`; the retained logs are `raw/preflight-main-normal.log` and `raw/preflight-main-optimized.log`.

## Measured action outcome

The exact public action result in `raw/interface_results-047e67d737ef4b889413a560669cf219.json` is `unknown`, with `input_dispatched=true`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. Producer completion receipts were unconfirmed at the action boundary. The fixture's independent event/effect records show that key `A` was accepted and text `a` appeared 6 seconds later (`raw/events.jsonl`, `raw/effect.json`). Since the lease expired after 2 seconds, the effect was observed about 4.05 seconds after expiry. This establishes a factual delayed fixture effect, **not** an authorized or eligible task success. No completion/effect oracle was registered in the public runtime.

The original action did not establish release or a late-input horizon. Its durable custody fence remained unresolved after the original MCP session closed. The first measured-run construction in `raw/runner.stderr.txt` failed after the public calls because the online adapter looked for completion-custody release/horizon timestamps that the UNKNOWN action did not contain. The exact result has no completion custody, so those values could not be supplied from that action.

## One-shot orphan recovery

After verifying the exact source operation, source generation, key obligation, absent producer PID, unresolved durable fence, and the still-live exact target, a fresh supervised-Win32 session obtained a no-input/no-authority public observation. Its generation matched the configured live target. Exactly one `interface_recover_orphaned_input` call followed; no task action was sent in the recovery session.

The public recovery receipt in `raw/orphan-recovery-api-attempt.json` reports:

- `recovered`, `release_confirmed=true`, with one returned virtual-key `A` key-up;
- neutral readback (`key_button_states=[false]`, `unicode_event_units=0`);
- late-input horizon verified for 2,000,000,000 ns, 78 observations, maximum observed gap 32,000,000 ns (limit 100,000,000 ns);
- source action preserved as `unknown`, `task_success=null`, and `replay_allowed=false`;
- durable source fence transitioned from unresolved revision 65 to clear revision 66, with the source generation fenced.

The original R24 fixture window was then sent a normal `WM_CLOSE`; evidence is in `raw/fixture-close-postmessage.json`. No manual journal edit or fence deletion occurred.

## Offline evidence join

The retained recorder journal, public action result, independent score, and
separate public orphan-recovery receipt were joined offline. The join verifies
the same source operation/generation, canonical source-custody digest,
independent final score, key-up/release receipt, neutral readback, full horizon,
and sample-gap bound. It derives **factual** fixture success `true`, effect
timing `after_authority_before_release`, and eligible task success `false`.
The original public action remains UNKNOWN, release-unconfirmed, and
replay-denied. The run covered 6.407 s of recorded task workflow and zero
model-delivered images; provider/model usage is unavailable because none was
used. This is not an efficiency comparison.

Existing `adapt_measured_run` correctly rejected this case: the exact source
results record still says cancellation is pending and has no confirmed release
or horizon. R24's later orphan recovery is a separate API attempt, so it cannot
be backfilled into that source record. The refusal is retained in
`raw/offline-adapter-refusal.json`. A separate research adapter now joins the
distinct recovery receipt without rewriting the source action; its seven
R24-bound positive/negative checks pass normally and under `-O`, including a
mutation check against the separately persisted raw public recovery report.
Implementation: `research/integration/standard_mcp_task_ledger_57_v1/orphan_recovery_effect_handoff_v1.py`;
tests: `test_orphan_recovery_effect_handoff_v1.py`. The reconstruction scripts,
derived run, join result, tests, and first failed preflight/reconstruction
attempts are retained under this packet's `raw/` tree. Rerunnable successful
outputs are [`offline-reconstruction-r04`](raw/offline-reconstruction-r04),
[`orphan-recovery-join-r05`](raw/orphan-recovery-join-r05), and the two
`raw/orphan-join-tests-*-r02.log` files.

## Runner and evidence notes

The first two recovery-runner starts stopped before calling the recovery API: the runner parsed the public observation at the wrong receipt nesting level. Their preflight failures are retained as `raw/orphan-recovery-preflight-failure.json` and `raw/orphan-recovery-preflight-failure2.json`. The parser was corrected, and the successful run wrote `raw/orphan-recovery-api-started.json` immediately before its single recovery call. The start marker plus public receipt provide the one-call audit trail.

The public action remains UNKNOWN even though factual fixture effect and later release/recovery are now established. Recovery does not promote the old action to task success. This trial narrows the composed boundary for expiry, delayed effect and bounded recovery on one owned Win32 fixture. It says nothing about general live GUI reliability, Calc/WSLc, MAP01, model-provider cost, matched efficiency, or Research Preview graduation.

## Next gate

Next run a finite repeated native standard-caller effect/recovery cohort against this exact R24 boundary before introducing a model/provider, keeping UNKNOWN source actions and separate recovery attempts explicit. Then continue with the current-main integration path called for by #57: freeze one same-workload, matched caller comparison with the standard and compiled/local-continuation routes, full all-attempt provider/token accounting, correctness/effect scoring, release and cleanup, and a live stale-dependency/refusal boundary. Reuse retained Calc and Chromium receipts only within their recorded scopes. Separately, #58 still needs its reproducible installable golden demo, reconstructable benchmark claims, accurate preview documentation, and a genuine MAP01 clear or explicitly unfinished showcase. Do not count R24 toward either acceptance gate.
