# Docker/Xvfb delayed-input recovery budget study (2026-10-29)

This study follows R71–R73's native Win32 positive movement trials and the prior Docker/Xvfb cancellation cases. It asks how bounded recovery behaves when a server interruption overlaps a queued delayed XTEST action. It is synthetic Xvfb evidence, not native Windows or MAP01.

## First outcomes

- **R01, default 4 s cancellation transaction window:** private Xvfb paused 4,000.406 ms; the queued XTEST delay was 8,000 ms. Public cancel returned `pending` in 309.992 ms. The transaction reached its deadline while Xvfb was resuming; owner disconnect and supervisor release were `UNKNOWN`. The harness stopped before its delayed horizon and fresh-task oracle. Test and Docker exit 1. Retained; no retry.
- **R02, 12 s test-only transaction window:** same 4 s pause and 8 s delayed request, with production default unchanged. Cancel returned `pending` in 308.204 ms; the 4,024.295 ms transaction confirmed owner retirement/disconnect and supervisor release readback; a separate client observed A/B up. No delayed B was seen at 8,501.965 ms and a distinct fresh-generation C task passed its 9-check oracle.
- **R02 old-task effect gate failed:** the original synthetic application recorded two additional A KeyPress effects at about +4,003.5 ms and +4,043.4 ms after cancellation. Its exact effect count was 3 instead of 1. A/B were neutral at the later horizon. The trace proves the duplicate effects, but does not identify whether X-server repeat or another queued transition caused them.

Both R02 runtime records remain conservative: old operation `runtime_failed`/`EOFError()`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, replay denied. Supervisor release readback and separate input observation do not rewrite the old-call contract. The fresh C task's success is distinct and does not clear the old fence.

This reveals two boundaries: the default recovery transaction can expire before recovery after the tested outage; extending only the test window allows release observation but still does not prevent a post-cancel duplicate effect. Next work should determine the duplicate source and implement/test a bounded guard that preserves the original task oracle. Do not call R02 a full task success or a production timeout change.

## Reproduction and custody

Private raw packets, conditions, preregistration, stdout/exit, Xvfb logs, observation images and source hashes are local under `private-packets/docker_xvfb_delayed_release_pause4000_*_currentmain_20261029_r0[12]/`. R01 and R02 have separate manifests. R01's first result remains unchanged. R02's source-only timeout override defaults to 4 seconds and is not wired to production callers.

The experiment used the pinned Linux/amd64 Docker image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, no network, read-only source/root, and a private writable output mount. It used explicit cancellation, not lease-expiry-only. One run per condition does not establish reliability or native transfer.

## Auto-repeat mechanism control (2026-10-29)

The separate enabled XTEST calibration observed auto-repeat mode 1 and two post-resume A presses 39.879 ms apart. The new one-shot disabled control r03 set/read back repeat mode 0, paused the same private Xvfb for 4,000.224 ms via pidfd, observed no repeated A presses, and read the keymap neutral after explicit release. This strengthens auto-repeat as a compatible explanation for the R02 duplicate-effect cadence (~39.872 ms), but does not establish the exact cause in the blocked MCP runtime or rule out queued/replayed transitions. R02 remains old-task-effect FAIL, runtime cleanup/release UNKNOWN and replay denied; its complete original structured raw was overwritten by a case-insensitive summary write, as documented in the local packet's `CUSTODY_CORRECTION.md`. The local summary, stdout and observation image remain; the original raw is unavailable. Disabled-control setup attempts r01/r02 stopped before keydown or Xvfb pause and are separately retained. See local `private-packets/docker_xvfb_autorepeat_disabled_paused_key_calibration_20261029_r03` and the supplemental [R03 note](AUTOREPEAT_R03.md).

## Standard-caller auto-repeat OFF control (R01, 2026-10-29)

The initial public-caller OFF trial R01 set/read back global repeat 0 but its setting process exited before the test; no in-run sampler exists, so do not treat R01 as a sustained OFF condition. The passive monitor run R02 using that lifecycle observed repeat=1 in all 1,147 samples and three extra A effects (count 4 vs 1). Persistent OFF control R03 kept the configuring client connected; repeat=0 in all 1,039 samples, the old-task count was exactly 1 and its oracle passed. The monitor gap was 4,002.561 ms across the Xvfb pause. Owner retirement, supervisor readback, independent release, fresh-C oracle, and final neutral keys passed; the old API still reports release/cleanup UNKNOWN, task_success null and replay denied. This supports active global Xvfb repeat as a contributor, but one sample per condition and the pause gap prevent an exact causal claim. See [the detailed R01–R03 comparison](AUTOREPEAT_PERSISTENT_OFF_CALLER.md) and local packets; R02 original full raw remains lost as documented above.

## Correction to the first repeat-OFF interpretation

R01 did not sample the setting during the test. The later R02 monitor observed mode 1 throughout, because the short-lived setter had exited before the caller started. R01 must therefore be treated as a failed sustained-OFF setup, not as evidence that mode 0 permits repeats. In R03 the setting client remained open; mode 0 was sampled throughout the available periods and no extra A effect occurred. See [the R01–R03 comparison](AUTOREPEAT_PERSISTENT_OFF_CALLER.md). The R03 monitor had a 4.003 s gap while the server was stopped, and the result remains one sample per condition.
