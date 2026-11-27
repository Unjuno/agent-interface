# Prestarted supervisor: earlier versus deadline-late private Xvfb resume

This packet corrects a regression introduced by PR #9974. That PR compared the old horizon key state to the state after close, overlooking an intentional intervening action: the harness creates a different client and presses `a`. The resulting b08 failure was a **test error**, not evidence of an unexpected new press. The corrected assertion requires the newer client's `a` hold to remain down after the old caller closes. The unchanged task oracles remain distinct and the earlier PR's README has a correction; its original raw files remain intact.

Three sequential isolated Docker/WSLc single attempts used the same pinned runtime subset, private synthetic Xvfb, 2 CPUs, 2 GiB, 256 pids and no network. All enabled the prestarted supervisor. B08 used the flawed assertion; b09 and b10 used the corrected test:

| Trial | Xvfb stopped | Old independent task | New client's hold after old close | Separate fresh task | Overall |
|---|---:|---|---|---|---|
| b08 | 254 ms | PASS | held as deliberately commanded | not reached due to invalid test assertion | FAIL |
| b09 | 254 ms | PASS | held | PASS | PASS, 5 tests |
| b10 | 4,043 ms, until transaction terminal | FAIL: `a` stayed down at old horizon | held | PASS | FAIL |

In b09 the prestarted worker recorded a verified release readback after the server resumed; the independent old-task oracle saw the expected effect and both monitored keys up through its horizon. Nevertheless the public cancellation retained `UNKNOWN`, `release_confirmed=false`, and replay denial. The test then explicitly pressed `a` as the newer client, confirmed old close did not release it, and **explicitly released that newer hold** before the fresh task. The fresh task is therefore conditional on harness cleanup and does not prove automatic recovery after an unresolved release.

The two timing conditions were not randomized, and this is one synthetic observation per corrected condition, not a reliability estimate, shared-display safety proof or MAP01 completion. In b10 the worker timed out with the server stopped; the old task failed even though a fresh task passed after manual cleanup. `public.zip` retains all three predeclared conditions, runners, logs and full receipts; `python audit.py` verifies hashes and classifications. Source subset and corrected test hashes are in the manifest; source and image bytes are not in the packet.
