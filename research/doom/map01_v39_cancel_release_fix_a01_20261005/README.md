# V39 cancel-release receipt repair A01

This is an additive v13 owner/v2 bridge candidate for the fake-display gap retained in `map01_cancel_release_measurement_a01_20261005`. InputOwner v13 stores the original `(program_id, step)` with each confirmed actuation. Cancellation cleanup samples each held key before and after `KeyRelease` plus `sync`, classifies the edge, and records a per-key receipt only against that actuation context. The bridge waits for the owner thread's post-cancel `input_state`, emits those receipts once, and clears its held ledger only after the owner reports an empty owned state or verified-empty cleanup.

Sampling failure still emits a per-key measurement row with an unconfirmed classification and no adapter edge; it never fabricates `CONFIRMED_PHYSICAL_UP`. The original v12 owner, v39 bridge, and A01 evidence remain unchanged.

TDD first reproduced both failures against the original v12/v39 implementation: no matching up row and stale `F8` in the bridge set. The candidate then passed 6 focused cancellation/ordinary-edge and real ExecutorV3 cancel-terminal tests, all 10 retained InputOwner owner-integration tests redirected to the candidate, and both existing v39 bridge tests. The ExecutorV3 trace contains one receipt in admission → cancel request → confirmed per-key up → verified terminal-release order; each release interval matches its pre/post keymap samples, and two-key IDs remain distinct. The read-only audit verifies baseline blob hashes, candidate hashes, and all 18 test receipts. The initial audit failed because it trimmed Git blob output before hashing; the error is retained. The corrected auditor passed first on 17 receipts, then again on the current 18-test set.

The ExecutorV3 integration fixture first stopped before admission because its synthetic lease lacked observed focus and intent binding; that HOLD construction output is retained, and the fixture was completed with the caller-observed values before the successful integration run.

The compatibility runner initially expected a V10 file beside the V12 fixture, while current main keeps V10 at `research/live_control/input_owner_v10.py`; the runner was corrected to use that canonical source before the successful 10-test run.

All tests use the repository's fake display. This package does not establish real X11 behavior, application consumption, useful feedback, bounded recovery efficacy, gameplay, MAP01 outcome, safety, latency, or live allocation. The candidate is not yet wired into a live MAP01 session.
