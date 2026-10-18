# A02 protocol — mutable owner-release receipt custody

## Question

Does the exact PR #7829 bridge preserve or upgrade a per-key release receipt when it drains an `owner_release` record while partial, then the owner mutates that same record to verified-empty after its aggregate query succeeds?

## H / T / D / C / U

- **H:** The bridge cursor advances when it drains the partial record. A later in-place aggregate update to `verified=true`, `keys_down=[]`, and `buttons_down=[]` will clear held state but will not revisit the record or upgrade/reissue its already-emitted per-key receipt. This remains true both for the expiry/cancel barrier and for a non-cancelled, unexpired `DecisionRequired` exit followed by Executor's release barrier.
- **T:** Two deterministic schedules run the exact PR #7829 bridge and owner in the current-main fake-Xlib harness. Both confirm one F8 down, fault only the subsequent per-key post-release keymap sample, gate the owner after it appends the partial mutable `owner_release` but before aggregate reconciliation, and consume the partial record before allowing aggregate reconciliation. Schedule 1 sets cancellation and runs the actual bridge `execute()` exit state barrier and final drain. Schedule 2 raises `DecisionRequired` without cancellation/expiry, lets execute-exit drain the partial record, then composes Executor's later release barrier. Because the fake base backend omits that production seam, Schedule 2 supplies only a test-side `release_all` composition that orders owner release, candidate drain, and neutral-state query.
- **D:** Each schedule must show the record was partial when consumed and later verified-empty, exactly one release receipt, a retained `PHYSICAL_SAMPLE_UNAVAILABLE` classification (not `CONFIRMED_PHYSICAL_UP`), no duplicate, and empty fake physical state. The second schedule additionally requires a verified `needs_decision` terminal with the original admission actuation ID joined to its one unconfirmed receipt. Any fabricated confirmation, duplicate emission, unverified terminal, or non-empty fake state fails this protocol.
- **C:** This is a deterministic single-process fake-display schedule. It demonstrates lifecycle/receipt behavior in the exact candidate bridge and owner sources; it does not estimate X11 timing or real-system frequency.
- **U:** No real X11, application consumption, task usefulness, threat-control effect, bounded recovery efficacy, gameplay, safety, latency, or live MAP01 allocation is established. It does not close Issue #59. The result is a negative candidate-mechanics finding, not evidence that a live user-visible key-up did or did not occur.

## Parallel-work and provenance controls

- Current main at test freeze: `563f636203ffd4c71e6a81968f6ad950dc53eaff`.
- Candidate under test: PR #7829 head `70c76483c46108bdd70bf2fb90679d948a5f156f`, fetched into a separate detached read-only worktree. Candidate files are SHA-256 locked in `SOURCE_LOCK.json`.
- The pre-existing PR worktree was observed clean only for the target files? No: its `test_cancel_release.py` was modified, and candidate source working copies differed from PR head. It was not used. The immutable GitHub PR-head checkout was used instead.
- No live allocation, GUI, game, or shared runtime was touched.

## Iteration record

1. Container launched; import stopped because sparse checkout omitted `research/live_control/executor_v3.py`. Added the exact current-main dependency path; no candidate assertion ran.
2. Fixture gate attached to an unused fake root; schedule timed out before aggregate reconciliation. Corrected the fixture to hold and patch the exact `screen().root` object used by the owner.
3. Attempt to exercise the bridge execute wrapper initially left telemetry context pre-set and hit the existing nested-context guard. Removed the test-side context setup so the wrapper owns it.
4. Callback assertions initially addressed the backend as though it were the unittest case. Bound assertions to the test case and reran.
5. Final container run exercised the actual candidate `execute()` wrapper and passed the cancellation/expiry custody assertions.
6. A second first attempt exposed that the fake superclass has no `release_all`; Executor therefore reported `failed` before the review's intended terminal. The harness was corrected with a test-only release-barrier composition (not a candidate modification).
7. Final rerun passed both schedules and the candidate's 12-test regression suite.

The first four attempts are test harness/setup errors, not candidate failures and not candidate passes. Their corrections and the successful exact run are retained here without treating the failed runs as semantic evidence.
