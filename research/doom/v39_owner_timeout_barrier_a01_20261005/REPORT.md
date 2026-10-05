# V39 owner-reply timeout under release barrier — A01

**Disposition: `FAIL_BARRIER_TIMEOUT_LEAVES_BRIDGE_STALE_AFTER_OWNER_STOP`.** The frozen V13 owner call returned its configured timeout after 1,989,094,800 ns. ExecutorV3 emitted one `failed` terminal with `release.verified=false` while the owner remained blocked. After the fake-display sync gate opened, the owner thread stopped with three owner-release records and the fake physical-key set empty, but the bridge ledger still contained F8 and the bridge had emitted zero `input_release_measurement` rows. The candidate summary did not retain the per-key classifications for those later owner records, so this result does not claim a confirmed-up edge was observed.

The timeout is bounded and the terminal fails closed. The failure is stale bridge state after owner shutdown; the run summary does not establish why the later owner records were omitted or whether one contained a confirmed-up classification. This forced schedule does not show how often the condition occurs on real X11.

The candidate ran once on native Windows CPython 3.11.9. The frozen source pair is current main `563f636203ffd4c71e6a81968f6ad950dc53eaff` plus the A08 release-barrier snapshot from PR #7805 head `61502e45d40b67b6d588b4e8357e42fde05a9dbe`. WSLc, Xvfb, ViZDoom, and the Docker Linux engine were unavailable; this is not container-equivalent or live-allocation evidence.

The read-only result audit passes the saved summary, exact captured stdout, and all 18 frozen file hashes. It does not independently sample an OS keyboard or re-run the candidate. Candidate stdout is retained in `TOOL_STDOUT_CAPTURE.txt`; structured result is `results/RESULT.json`. Reproduce the saved-result check with `py -3.11 audit_result.py`. Do not rerun A01.

No live X11, OS input, game/task effect, model, independently useful feedback, threat exposure, bounded recovery efficacy, latency distribution, safety rate, or MAP01 result was tested. The #59 live gate remains open and separately unassigned.

## A03 successor: release completes after bounded wait

The A02 late-drain candidate was challenged at its 1.5 s owner-stop wait boundary. See [`a03_post_bound/A03_REPORT.md`](a03_post_bound/A03_REPORT.md). The forced schedule shows the expected limitation when the owner remains blocked past the wait: physical up is later confirmed in the fake backend, but the bridge retains F8 and emits no release row; ExecutorV3 remains failed/unverified. This is not evidence about real X11 frequency or live MAP01 behavior.
