# Standard-caller Xvfb release-supervision diagnostic — r01

## Frozen run and custody

- GitHub Actions run [39444638512](https://github.com/Unjuno/agent-interface/actions/runs/39444638512), manually dispatched on `main` at source SHA `87740c81bf687081d7e2df1c8c4c57c0d6fd1ba5`.
- Workflow: `.github/workflows/runtime-x11-v1.yml`; runner: `ubuntu-latest`; private Xvfb package `2:21.1.12-1ubuntu1.9`.
- The run exited 1 at `Run private Xvfb integration`. All six artifact uploads completed. The downloaded JSON and PNG files are retained here unchanged; `SHA256SUMS` covers each retained raw file.
- This is a fresh workflow run, distinct from the previous run 39376306302. It uses synthetic Xvfb tasks, not WSLc, physical desktop input, or MAP01.

## Conditions and outcomes

The workflow exercised standard-caller target-generation/recovery, a blocked owner in `Display.sync()` while Xvfb stayed responsive, four cancel-retirement trace comparisons, whole-Xvfb stop, XRes disconnect fencing, and held-key disconnect ordering.

The primary blocked-owner case returned cancel in 962.216 ms. The PID-qualified disconnect readback took 83.669 ms; the independent release worker took 618.668 ms and read both keys up. The independent synthetic-task oracle passed: the initial effect remained `[1]`, no delayed `b` press appeared, and both keys were up at the 8.503 s horizon. The runtime receipt conservatively remained `cancel_unconfirmed`, `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`.

The four cancel-retirement comparisons were mixed: two passed the independent synthetic oracle and release readback (642.408 ms and 634.328 ms release-worker durations); two failed with `worker_did_not_exit_cleanly` and exit code `-15` (692.538 ms and 698.831 ms total worker durations). The failing supervisor receipts omitted the worker result payload and status, so this run cannot establish whether either killed worker had already returned a verified release result. The passing cases also retain runtime `release_confirmed=false`, cleanup `UNKNOWN`, and replay denied.

The target-generation/recovery scenario passed its scoped integration contract: stale generation was refused, recovery release was read by an independent X client, and a subsequent synthetic action produced independently observed property `[3]` in 55.451 ms. The recovery action's separate synthetic effect was `[2]` in 66.256 ms. `runtime_task_success_api` remained null; these are independent synthetic oracles, not MAP01 success.

The whole-Xvfb-stop case failed its task oracle. The caller remained unconfirmed, post-resume cleanup was `UNKNOWN`, and replay was denied. This is a separate platform-outage boundary from an owner blocked while the server remains responsive; it does not prove bounded release during server unavailability.

## Diagnosis and next discriminator

The two trace failures reported `worker_did_not_exit_cleanly`. In `supervise_xres_worker`, a received result is followed by only the configured 100 ms clean-exit join; if the child remains alive, it is terminated and the result is reduced to `UNKNOWN`. The old failure receipts do not preserve the child's result status, so attributing those two cases to a verified result being lost would be speculation.

The accompanying code change adds the worker-reported status, parent receipt time, observed exit time, and elapsed post-result shutdown time to the supervisor receipt. It does not promote a forced termination to success. A fresh Xvfb run on that instrumented source is needed to tell whether the two cases returned `released` before shutdown stalled or returned another status. Any later grace adjustment must remain finite and preserve the caller's 3 s cancellation bound. Whole-server-stop release, physical input, MAP01, cross-run reliability, and matched efficiency remain unproven.
