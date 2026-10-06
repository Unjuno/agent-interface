# Current-v39 owner-cleanup composition control

## H / T / D / C / U

- **H:** When cancellation becomes visible after the transition wrapper snapshots the lease but before the v10 owner dequeues the queued `up`, the real v39 typed backend still emits the per-key batch receipt with `owner_transition_verified=false` after observing owner cleanup.
- **T:** Instantiate the committed `doom_typed_release_backend_v3.Backend` against the exact `input_transition_owner_v3` source from PR #7376 head `4dacf68632b686948c0c2dee6742ffa67dc13efb` and `input_owner_v10` from main `f11ee9d051239094cf3679e19c80bd7deaed0564`. The owner thread is real; Xlib/XTest are deterministic fakes. A `RaceCancel` returns false for the caller's first lease snapshot, then exposes cancellation. The fake owner call gate waits for the owner cleanup record before dequeuing `up`.
- **D:** Pass requires one admission; one verified owner cleanup with reason `cancelled`; exactly one XTest KeyRelease from cleanup; a single emitted per-key transition row with `owner_cleanup_intervened=true`, `ordinary_release_candidate=false`, empty post-owner state, and `owner_transition_verified=false`; and no key left down. The independent auditor also rejects a mutation that marks the transition verified.
- **C:** The backend source is real but its base hold sequencing is a small test double. Xlib/XTest and the X server are faked; this does not test a live X server, physical key state, application consumption, task effect, or latency.
- **U:** One key, one cancellation interleaving, one Linux owner implementation exercised as Python on macOS with fake Xlib; no cross-platform or live-runtime transfer claim.

The first harness setup attempt is retained in `setup-attempt-01.txt`; its fake pointer omitted `root_x/root_y` and raised before the candidate receipt was written. The corrected recorded run is in `candidate.raw.json`. This is a construction composition control, separate from the stopped X11 allocation; it performs no real input.
