# A02 formal capture — `STOP_RUNNER_FAILURE`

Allocation `BLACKWELL-OBSERVATION-DOMINANCE-6678-T1-ORB-A02-20261003-01` was preregistered on Issue #6678 before formal invocation. It is permanently stopped and must not be rerun.

The capture container was created and started once with the preregistered pinned Playwright image and isolation limits. Chromium did not launch and no scheduled fixture capture began. Node exited 1 with `EEXIST: file already exists, mkdir '/out'`: `/out` is already present as the writable bind mount, but `capture.mjs` tried to create it as a new directory. Container ID and pre/post `docker inspect`, exit marker, stdout and stderr are retained in `construction/a02-postmortem/` and `formal_01/`. Formal stages: capture invocation 1 (failed before capture), candidate 0, auditor 0, retries 0. No scientific observation or hypothesis verdict was produced.

The runner defect is corrected in the current local source by removing that redundant mountpoint mkdir. That correction does not authorize another invocation under A02: a rerun would violate the frozen one-shot allocation. A future attempt must use a distinct successor allocation, new output namespace, reviewed source hashes and new preregistration. The runner now exits at the prior failing point for A02, so no later-stage output was overwritten or substituted.

Local environment/readiness suite before formal run: 5/5 tests, Python compilation, Node syntax, shell syntax, analysis index, workspace index and `git diff --check` passed. This validates the test/package scaffolding only; it does not override the formal STOP.

## H / T / D / C / U

- **H:** Untested for this empirical fixture. A02 produced no samples.
- **T:** The intended 72-capture, three-state OrbStack/Playwright experiment did not begin; the only formal execution was the failed container startup/entrypoint sequence.
- **D:** `STOP_RUNNER_FAILURE`, not PASS or scientific FAIL. Candidate and auditor were not invoked.
- **C:** Local tests did not exercise the actual bind-mounted output-directory entrypoint; the construction smoke used a different command and did not detect this mismatch.
- **U:** No claim about browser observation channels, Agent Interface runtime, models, effects, safety, latency, or product behavior.
