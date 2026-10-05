# A03 protocol: late per-key physical-up resampling

## H — Hypothesis

After an unexpired `DecisionRequired`/focus-invalid exit, a release measurement that failed immediately may still be recovered safely if the owner thread later obtains a per-key sample proving the key is up, the earlier per-key sample proved it down, and release plus synchronization occurred between those samples. The receipt must remain available until reconciliation is complete. Aggregate empty state alone is not sufficient evidence.

## T — Treatment

Run the exact PR #7829 candidate as baseline and isolated experiment-only copies of its owner and bridge modules as treatment. The treatment retries the specific key sample after aggregate reconciliation and defers draining a mutable, unverified owner-release receipt. A failure-injected retry is the negative control. Tests use a synthetic Xlib harness and a test-only release barrier; no GUI/game or live input is exercised.

## D — Decision rule

PASS only if baseline remains unconfirmed; treatment emits one matching-actuation `CONFIRMED_PHYSICAL_UP` receipt with the bracket `[pre_sample.finished_ns, late_sample.finished_ns]`, ordered across release/sync and before `needs_decision`; authority and application-consumption claims remain false; and the retry-failure control remains `PHYSICAL_SAMPLE_UNAVAILABLE` with no bracket. Any fabricated confirmation, identity mismatch, bad interval, duplicate receipt, or missing terminal ordering is FAIL.

## C — Confounds / limits

This synthetic harness does not establish X server behavior, GUI/game consumption, task success, production integration, latency, or live allocation. The test-only release barrier models ordering but is not a claim that the production executor has this barrier. Host disk reports 100% capacity (14 GiB available); cgroup swap limit equals the 1 GiB memory limit, so swap is not claimed disabled. Container reports linux/aarch64; CPU quota is 100000/100000, memory.max=1073741824, pids.max=64.

## U — Uncertainty / next work

The result is only a mechanism-level synthetic observation and does not satisfy Issue #59's live-path exit condition. Independently review the event-custody mutation and repeat under a production-equivalent release barrier before relying on the result. Keep Issue #59 open.
