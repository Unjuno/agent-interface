# WSLc portability check C04

This is a one-shot CPU-only, network-disabled construction check of the C03 cancellation/publication integration regression under the pinned local Python image. It was selected after a fresh WSLc running-container snapshot returned empty. It is not a MAP01 allocation and does not invoke a game, model, GUI, or physical input.

## H / T / D / C / U

- **H:** The real ExecutorV12 + transition-owner-v4 + input-owner-v12 fake-Xlib integration test passes under the pinned Linux Python image as it did on Windows CPython 3.11.9.
- **T:** Freeze exact source SHA-256, image digest, full WSLc command, and run/output paths. Run once with `--network none`, `--cpus 1`, `--memory 512M`, read-only source, and no pull. Retain first raw output and exit code.
- **D:** PASS only on exit 0, one test run and final `OK`; any nonzero exit or missing output is FAIL/HOLD. No retry.
- **C:** An OS/runtime mismatch or unavailable Python/API could fail despite correct source behavior. Fake Xlib and the controlled thread schedule do not represent real X11 scheduling.
- **U:** This says nothing about GUI/X11, MAP01, scorer, app-server, useful feedback, recovery latency, matched performance, WSLc hard memory enforcement, or live research success.

See `FREEZE.json`, `RUN.json`, `RAW.stdout.txt`, `RAW.exit.txt`, and `AUDIT.json` for exact identity and outcome.

The test passed once (1/1). WSLc emitted the host's existing swap/cgroup warning; the requested 512 MiB limit is not evidence of enforced memory isolation. The post-run running-container query returned no rows. This portability check ran before the branch was merged with the then-current main; its frozen source hashes remain identical after that merge.
