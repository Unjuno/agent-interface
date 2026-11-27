# MAP01 expiry recovery and task effect R160–R161 (2026-11-13)

## R160 — runner failure retained

R160 reached one live dispatch and showed W still down 8.000 ms after the
deadline, but the research runner raised after dispatch: the frozen packet
omitted `capture_timing_audit.py`, and the independent screenshot path passed a
full frame to the patch-only classifier. Its original hold and raw result remain
unchanged. The additive post-run audit recovered the ROI transition from the
retained frame, but lacked that runner path's capture identity/timing join.
R160 is not silently upgraded to a clean runner pass.

## R161 — one fresh native integration trial

R161 used current source commit `72d8bcdc8fb4b4e7fd12c95394d21fde45aa3a12`,
the pinned Windows CPython 3.14.2/QPC environment, one fresh MAP01 process, one
public compiled dispatch, and the same 20 ms expiry boundary. Its research
runner includes the full-frame ROI call and the capture timing audit module.
Preflight, Computer Use target gate, frozen verification (56 checks), and
post-run file manifest all passed. The target exited normally and the final
custody/input state was clear/neutral.

The single operation was `call_id=d67dd4f9228f45e1ba0e5f45239acfe5`,
`operation_id=f0f604d866694d4996299dfd32107687`, generation
`1ace6c001e09f3d620c4bc653e4e7fdb4e2d56c1730b816ff070b0c95b296ccb`.
The public result remained `SAFE_YIELD/delivery_uncertain`; task verification
separately returned success for the pre-expiry pistol action. Public and
independent image evidence both classified 50→49. The independent effect
report itself left `operation_id` null; the additive audit joins its exact
call ID and generation to the unique operation in the raw public receipt. The
frozen report was not edited.

### Deadline, release, and ordering

- The QPC bracket from fully pre-deadline W-down to fully post-deadline W-up
  was 8.1086 ms, within the frozen 20 ms limit. W remained sampled down for
  5.9882 ms after the serialized deadline.
- Caller/supervisor cancellation began about 0.244 ms after expiry and returned
  about 0.290 ms after expiry. The phase-only custody `cancel_pending` write
  started about 0.304 ms after expiry and returned about 7.370 ms after expiry.
- The recovery exchange started about 4.923 ms after expiry. Two
  operation/generation-bound native `SendInput` spans returned at +6.825 ms and
  +7.350 ms; their measured durations were 0.411 ms and 0.494 ms. The public
  release receipt arrived at +18.388 ms. The spans prove API call intervals and
  insertion return values, not application consumption; their two individual
  obligations are not distinguished by the retained span fields.
- The `cancel_pending` write overlaps recovery. The source orders supervisor
  cancellation before this phase-only write because admission already
  persisted the unresolved custody row before producer start. If the phase
  update fails, the prior unresolved row is retained; only the verified
  recovery path can resolve it. This is the tested source contract, not a claim
  that the new phase itself was durable before SendInput.
- Stage-trace decomposition localizes the observed cancel-to-recovery delay:
  `supervisor.cancel` began at QPC `319515411210600`; producer retirement ran
  from `319515411342000` to `319515416081700` (4.7397 ms); the recovery
  exchange began at `319515416137100` (4.9265 ms after cancel start), only
  0.0554 ms after retirement returned. Thus producer retirement accounts for
  nearly all of this single-run interval. This is instrumentation evidence,
  not a distribution or a finding that the wait is unnecessary. Retiring the
  producer before UP preserves the no-more-input boundary; optimization would
  require proving equivalent fencing under a late producer write.
- Same-generation readback confirmed W and mouse-left neutral. The recovery
  late-input horizon covered two seconds with 78 observations and a largest
  observed gap of 31.679 ms. A separate neutral horizon had 176 observations
  and a largest sample gap of 12.844 ms.

### Effect and delayed command

The exact public capture audit passed its request/receipt/time ordering checks.
The independent full-frame screenshot changed 50→49 using the frozen
`(470,778)-(510,808)` ROI. Same-run demo adjudication returned
`PASS_SCOPED_NO_RECORDED_FORWARD_COMMAND`: no recorded forward-command tics
were found after expiry before release or after release through the conservative
two-second horizon.

The R161 templates are different from the older general-purpose
`ammo_49_template.png`/`ammo_50_template.png` already in this directory. Using
those older templates on the R161 frames correctly returned `unknown`; it was
not evidence that the R161 frame result was wrong. The R161-specific templates
are now retained under `r161_frozen_templates/`, with their exact hashes pinned
by the tests. Re-running the new full-frame API against the exact retained
R161 frames and templates reproduces 50→49.

## Decision and next discriminating work

R161 is one scoped native pass for expiry-boundary observation, recovery, task
effect, and the recorded-demo command interval. It does not estimate
reliability, establish a hard latency bound, prove that the application
consumed every inserted event, exclude every queued OS message or other input
type, establish MAP01 completion, or provide the matched efficiency accounting
required by Issue #57. Keep this evidence out of the Calc token/latency arms.

The next discriminator is whether the producer-retirement wait is required by
the actual process/custody fence and whether local tests already prove that
ordering for a still-running or delayed producer. First map the exact retirement
wait path and its existing blocked-producer tests; do not shorten it on timing
alone. If the local proof leaves a real uncertainty, preregister a fresh native
replication with the same expiry gate and separate timestamps for retirement
begin/end, recovery exchange, first native UP, readback, and task effect. Keep
the 20 ms gate and every failed/unknown outcome. Multiple runs would be needed
to characterize a distribution. Do not infer a runtime regression from this
single instrumented run.

### Follow-up source/test audit

Current source enters `_retire` when cancellation leaves input obligations or
late server requests possible, and only then runs the disconnect-gated cleanup
path. `_retire` terminates and joins the exact producer, escalates to kill if it
survives the terminate grace, and records retirement separately from release.
The targeted regressions
`test_cancel_retires_owner_when_response_keeps_input_and_late_request_possible`
and `test_retire_kills_owned_process_that_ignores_terminate` passed 2/2 under
normal and optimized Python. These deterministic tests support the ordering
contract; they do not measure native process retirement latency. No runtime
change is justified by R161's single 4.74 ms retirement interval.

## Evidence custody

The immutable conditions, raw frames, receipts, stage traces, demo, and original
decisions remain in the task-local `work/map01-native-r161-candidate/` packet;
the additive audit is `postrun-addendum-r161/`.

- R161 run manifest: `POSTRUN_SHA256SUMS_R161.json` (83 files, verified).
- R161 additive manifest: `postrun-addendum-r161/R161-POSTRUN-ADDENDUM-MANIFEST.json`
  (8 files, verified).
- Final scoped adjudication SHA-256:
  `e8fdb7664b930e675b1a711c5a55d140db71965f00ad19c41ff9a2d4696b7878`.
- The initial post-run script's three audit-query mistakes remain preserved in
  the addendum; the independent corrected v2 adjudication passes 17/17 without
  overwriting the initial report or the runner's `PENDING_DEMO_ADJUDICATION`.
