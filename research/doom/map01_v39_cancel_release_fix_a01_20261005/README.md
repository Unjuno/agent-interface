# V39 cancel-release receipt repair A01

This is an additive v13 owner/v2 bridge candidate for the fake-display gap retained in `map01_cancel_release_measurement_a01_20261005`. InputOwner v13 stores the original `(program_id, step)` with each confirmed actuation. Cancellation cleanup samples each held key before and after `KeyRelease` plus `sync`, classifies the edge, and records a per-key receipt only against that actuation context. The bridge waits for the owner thread's post-cancel `input_state`, emits those receipts once, and clears its held ledger only after the owner reports an empty owned state or verified-empty cleanup.

Sampling failure still emits a per-key measurement row with an unconfirmed classification and no adapter edge; it never fabricates `CONFIRMED_PHYSICAL_UP`. The original v12 owner, v39 bridge, and A01 evidence remain unchanged.

TDD first reproduced both failures against the original v12/v39 implementation: no matching up row and stale `F8` in the bridge set. A separate regression reproduced a third loss path: the owner had recorded cleanup, but an exception from the subsequent `input_state` reconciliation prevented the bridge from draining the receipt. The fix now drains in `finally`, preserving measurement while the state error still propagates and does not falsely claim successful reconciliation. The candidate passes 9 focused cancellation/ordinary-edge, reconciliation-failure, expiry-exit drain, and real ExecutorV3 cancel/expiry terminal tests, all 10 retained InputOwner owner-integration tests redirected to the candidate, and both existing v39 bridge tests. The ExecutorV3 trace contains one receipt in admission → cancel request → confirmed per-key up → verified terminal-release order; each release interval matches its pre/post keymap samples, and two-key IDs remain distinct. The read-only audit verifies baseline blob hashes, candidate hashes, and the currently audited test receipts. The initial audit failed because it trimmed Git blob output before hashing; the error is retained. The corrected auditor passed first on 17 receipts, then again on the earlier 18-test set; the current audit is rerun below.

The ExecutorV3 integration fixture first stopped before admission because its synthetic lease lacked observed focus and intent binding; that HOLD construction output is retained, and the fixture was completed with the caller-observed values before the successful integration run.

The compatibility runner initially expected a V10 file beside the V12 fixture, while current main keeps V10 at `research/live_control/input_owner_v10.py`; the runner was corrected to use that canonical source before the successful 10-test run.

All tests use the repository's fake display. This package does not establish real X11 behavior, application consumption, useful feedback, bounded recovery efficacy, gameplay, MAP01 outcome, safety, latency, or live allocation. The candidate is not yet wired into a live MAP01 session.

The complete candidate package was also replayed on a disposable overlay of main at the prior replay `6750ab3843bdcd7eb221dedfb3dd0ae3f184f38d`; all 7/10/2 suites, the source audit, the 41-file package checksum set, and `git diff --check` passed. The raw command output is in `current-main-replay.log`. This verifies composition on that exact source tree only and remains fake-display evidence.

After main advanced to `16c74566b64f32d7fe035c7724bcfe3865863a91` (r135), the selected owner, bridge, Executor, and lease source blobs remained unchanged. The candidate delta was replayed on a detached tree at that exact main SHA: candidate 7/7, owner compatibility 10/10, bridge 2/2, source audit, all 43 then-listed checksums, and `git diff --check` passed. Full output is retained in `current-main-r135-replay.log`. This is source composition evidence only, still using a fake display.

A subsequent expiry-path probe showed that owner cleanup can complete without setting `lease.cancel`. The bridge now drains already-recorded owner-release rows on every `execute()` exit, while the ordered `input_state` reconciliation remains cancellation-specific. A real fake-display owner test performs a key admission, completes owner `release`, then raises `Expired` with the cancellation event clear; the earlier bridge emitted zero up receipts and retained F8, while the fix emits the confirmed contextual receipt and clears the bridge ledger. This does not characterize cleanup that is still pending after the exit boundary.

The expiry-path regression is retained RED/GREEN and included in the current 20-test source-locked audit. A fresh r135 composition replay for this revision is recorded separately as `current-main-r135-replay-a02.log`.

Current r135 replay A02 includes the expiry-exit regression (8/8 candidate tests), 10/10 owner compatibility tests, 2/2 existing bridge tests, source audit, and then-current package checksums. The complete output is `current-main-r135-replay-a02.log`; `RESULT.md` states the exact remaining race boundary.

A real ExecutorV3 expiry path is now covered over the fake display: the lease expires while F8 is held, InputOwner independently releases it, ExecutorV3 terminates as `expired` without setting the cancellation event, and the bridge emits one contextual `CONFIRMED_PHYSICAL_UP` before a verified-empty terminal. The regression failed against pre-fix candidate `518871e9` with zero up receipts and passes after unconditional draining. `executor-expiry-red.log` and `executor-expiry-green.log` retain the paired results.

This raises the focused set to 9 and total source-audited receipts to 21. The r135 replay A03 record replays this expiry integration test on current main.

The added real ExecutorV3 expiry-terminal regression was replayed on the same detached r135 main tree `16c74566b64f32d7fe035c7724bcfe3865863a91`: candidate 9/9, owner compatibility 10/10, bridge 2/2, the 21-receipt source audit, then-current SHA256 list, and full-PR `git diff --check` pass. Raw output is `current-main-r135-replay-a03.log`.

Main subsequently advanced to `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30` with V13/ExecutorV12 cancellation composition. The selected frozen owner, V39 bridge, ExecutorV3, and lease source blobs remain identical to the lock; the lock was refreshed to this main. The candidate delta replay at this exact main SHA passes candidate 9/9, owner compatibility 10/10, existing bridge 2/2, source audit, then-current package checksums, and full-PR `git diff --check`. Raw output is `current-main-post-r135-replay-a04.log`. This adds composition evidence only, not a live result.

The candidate is also exercised through current-main ExecutorV12 (main `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`), which is the current composition path used by PR #7811. A 30ms lease expires while F8 is held; V13 InputOwner performs expiry cleanup; the bridge emits one confirmed contextual per-key up before ExecutorV12 emits an `expired` terminal with verified-empty aggregate release. No cancellation event is set. The independently captured current-main composition test is kept in `test_executor_v12_expiry_composition.py`, and its one-test output is audited separately from the nine candidate unit tests.


The complete current-main replay, including the V12 expiry composition test, passed at `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`: 9 candidate tests, 1 V12 composition test, 10 owner compatibility tests, 2 bridge tests, and the 22-receipt source audit. The final replay record is `current-main-post-r135-replay-a05.log`; the package checksum manifest covers retained evidence and source files. This adds fake-display composition evidence only.


## A06 — preserve release measurements across aggregate-query failures

**H:** After a confirmed per-key up, an aggregate `query_pointer()` or `query_keymap()` failure can occur before the candidate owner stores the per-key measurement.

**T:** Deterministic fake-display regressions admit F8 with a program/step identity, execute owner cleanup, and inject each aggregate-query fault after the per-key pre/post keymap samples. The unfixed candidate loses the bridge release row in both cases.

**D:** PASS requires the confirmed context/actuation-bound up row to remain drainable, the owner-release record to remain explicitly `verified=false` without fabricated aggregate fields, and the original query error to propagate. The two tests failed against pre-fix PR #7805 candidate commit `32686927ce6b07a035beb4c0297171a1f951c6c6` and pass after the record is appended before aggregate queries.

**C:** A transient one-shot query failure followed by a successful ordered `input_state` query can reconcile the bridge's aggregate held set; this does not establish what real X11 does or how often queries fail.

**U:** Fake display only; no real X11, application consumption, useful feedback, bounded recovery, gameplay, safety, latency, or live MAP01 allocation.

Current main advanced to `bfd182727aebd9636c6a84fb437848c1dfe66be8` via the typed-observation epoch-alias repair. The frozen owner/bridge/Executor inputs are source-locked at that exact main. The refreshed overlay passes 11 focused candidate tests, 1 ExecutorV12 expiry-composition test, 10 owner compatibility tests, 2 bridge tests, and the source-locked 24-receipt audit. RED/GREEN logs and full replay are retained in `aggregate-query-red.log`, `aggregate-query-green.log`, and `current-main-post-r135-replay-a06.log`. PR #7805 remains a draft research candidate; no runtime code was promoted.


## A07 — preserve owner-query-fault receipts through ExecutorV12 expiry

**H:** When V13's expiry cleanup confirms F8 up but an aggregate pointer or keymap query fails, the V2 bridge must still publish the `expired` contextual per-key up. ExecutorV12 may emit its `expired` terminal only after its later release barrier verifies empty owner state.

**T:** On exact main `bfd182727aebd9636c6a84fb437848c1dfe66be8`, run two fake-display V12 compositions. Let the owner deadline loop release F8, inject one failure into either aggregate `query_pointer()` or aggregate `query_keymap()`, and let ExecutorV12 perform its final release barrier. Require one context-bound `CONFIRMED_PHYSICAL_UP` with reason `expired`, an explicitly unverified partial owner record for the failed query, one expired terminal with verified release, and empty fake/backend-held state.

**D:** Both integrations failed against pre-fix candidate commit `32686927ce6b07a035beb4c0297171a1f951c6c6` because the `expired` receipt count was zero. Both pass with the record-before-query repair.

**C:** The V12 final barrier can perform a later successful aggregate check; that recovery does not replace the missing causal key-up receipt. This is a deterministic fault path, not an estimate of live X11 query failure frequency.

**U:** Fake display only; no real X11, application effect, useful feedback, bounded recovery efficacy, gameplay, safety, latency, or live allocation.

The current-main suite now includes 11 focused candidate tests, 3 ExecutorV12 composition tests (2 query-fault cases), 10 owner compatibility tests and 2 bridge tests. The source-locked auditor validates 26 receipts. RED/GREEN output is retained in `executor-v12-query-fault-red.log` and `executor-v12-query-fault-green.log`; exact-main replay is `current-main-post-r135-replay-a07.log`.

## A08 — close post-execute expiry arrival and classify duplicate NOOP up

**H:** InputOwner expiry cleanup can occur after ExecutorV3's execute-exit drain but before its terminal release check. That late key-up must be emitted exactly once before a verified-empty terminal. A later raw up that finds the key already released must remain diagnostic, not a second release measurement.

**T:** A deterministic owner-thread barrier holds cleanup until after the execute drain; the regression requires no early receipt, then one context-bound confirmed up after the terminal release barrier and before `expired`. A separate async-cleanup/raw-up test requires an `input_release_noop` diagnostic followed by exactly one confirmed release measurement.

**D:** Both tests fail against the PR's pre-barrier bridge: the expiry terminal has zero released-up rows, and duplicate raw up is emitted as another release-measurement row. Both pass with the candidate bridge's ordered owner release barrier, record drain in `finally`, and NOOP event remapping. The deadline-aware owner release reason also keeps an expiry cleanup initiated by the final barrier classified as `expired`.

**C:** This closes the deterministic fake-display post-drain ordering and duplicate-row cases in the tested ExecutorV3/ExecutorV12 composition. It does not estimate live race frequency or establish X11 behavior.

**U:** No real X11, application consumption, independently useful feedback, bounded recovery efficacy, gameplay, safety, latency, or live allocation. Issue #59 remains open.

Bundled CPython 3.12.14 verification at exact main `bfd182727aebd9636c6a84fb437848c1dfe66be8`: candidate 12/12, optimized repeat 12/12, ExecutorV12 compositions 3/3, owner compatibility 10/10, and V39 bridge 2/2. The source audit checks 27 primary test receipts plus the optimized repeat. RED/GREEN pairs are retained in `post-drain-red-current.log` / `post-drain-green-current.log` and `noop-row-red-current.log` / `noop-row-green-current.log`.
