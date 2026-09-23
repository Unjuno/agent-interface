# Native overview re-anchoring: retained container result

**Disposition: scoped local-task PASS for v2; MAP01 clear and general GUI efficacy not tested.**

Coordination: Issue #298. Repository publication base is `ed04bba63813ddfa508912eaaadcdca87d59600b`; the restored runtime dependency bundle is pinned to `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. All 2,592 source hashes and 12 wheel hashes matched the supplied manifest. No previous automap-controller program or running experiment survived in this container. Earlier chat-only navigation/clear numbers are not imported as verified evidence.

## Executed work

A controlled-mode ViZDoom probe delivered Tab through InputOwner/XTEST but did not expose an automap. Its first clock read was stale; a separately versioned probe refreshed state before/after the wait and observed 59 tics over 1.686 seconds. The same executable launched as an ordinary native game did display its map through Tab. That is a distinct launch condition, not a repair to the frozen shared MAP01 controller.

The experiment therefore uses native process launch, X11 screenshots, and bounded InputOwner v10 keyboard calls. It never reads an auxiliary automap/screen buffer, position, angle, labels or engine action API. The task is deliberately local: translate the observed structural map by -12 pixels, then return to its initial visual anchor. This does not test level completion or unknown-map route planning.

The same controller is used without a domain-specific control branch on a Tk diagram-pan task. Three GUI layouts use seeds 1261/1262/1263 and gains 30/45/65 pixels per second. Native Doom pair IDs are labels, not controlled engine RNG seeds. Each domain has three fresh pairs in alternating order.

The replay control applies six 80 ms forward pulses and six backward pulses. The closed-loop candidate compares each screenshot to the original anchor, proposes a short pulse, releases it, and checks the result. V2 requires another screenshot after 150 ms of input-free settling before accepting a goal. Local pulse duration is 30 ms near the goal and 80 ms otherwise. The independent endpoint tolerance is 2.5 pixels; maximum actions are 24 per phase.

## Retained result

| Domain / strategy | Both phases and final endpoint | Final absolute image error | Episode wall time, median [range] |
|---|---:|---|---|
| Native MAP01 / replay | 0/3 | 7, 8, 4 px | 1.916 [1.899, 1.916] s |
| Native MAP01 / closed loop | 3/3 | 2, 2, 0 px | 2.615 [2.447, 3.152] s |
| Rendered GUI / replay | 1/3 | 0, 1, 1 px | 1.918 [1.899, 1.929] s |
| Rendered GUI / closed loop | 3/3 | 1, 1, 1 px | 1.657 [1.328, 1.896] s |

Returning to the origin alone is insufficient: GUI replay returned but missed the outbound target in two cases. All 12 completed v2 episodes have verified empty releases and terminal owner state. All 154 input-admission/release pairs are retained in the endpoint evidence. There are 24 **offline** missing/changed-shape refusal checks; these are not live interruption tests.

The native image scorer is a separate spatial-template registration implementation, not the controller's Fourier phase correlation. It checks the actual endpoint masks. GUI evaluation additionally uses app-state samples read after the controller has exited. This is separation of code/dataflow within the same container, not an OS-enforced confidentiality boundary. Native scoring is image-relative, not a hidden engine-position oracle.

## Negative results and repairs

- The first environment probe failed during Xvfb readiness because of inherited Xauthority context. An explicit empty Xauthority file for the private access-control-disabled X server allowed startup. TCP listening is disabled.
- A native startup probe initially searched for the wrong title capitalization. That failed first attempt is retained in the full archive.
- V1 native closed loop appeared to reach the goal in 3/3 cases but passed the later final endpoint in only 2/3. Return errors were 1, 3, 1 pixels. It must not be described as 3/3 persistent completion.
- GUI v1 failed before task input because the inherited wmctrl client-list discovery did not list an actually visible Tk window. Three arms timed out; the fourth was interrupted by the outer execution budget; the last two did not start. All are preserved, not silently replaced by v2.
- V2 changes public X11 discovery to require one visible named client in the window tree, and adds the settle/recheck rule. The gate and task dynamics remain hash-identical. The v2 plan and hashes were recorded in Issue #298 comment 5690453249 before execution.
- The initial endpoint replay verifier expected `target_dx` in a settled-check row where the runner did not record it. The verifier was repaired to use the already frozen phase targets. Experimental bytes and results were unchanged. Its earlier source is retained in the source archive.

## Environment and checks

Linux 6.18.44, CPython 3.13.5, AMD EPYC 9V74 (five CPUs in process affinity; actual clock not pinned), OpenCV 4.13.0, NumPy 2.3.5, ViZDoom 1.3.0, Xvfb 1280x800x24, Openbox, 640x480 application client. One arm runs at a time, with a separate application process and input-owner thread. Measurements include image capture, PNG retention and driver overhead. No frontier-model call or token-saving measurement occurs.

Seven controller tests pass. Independent lossless endpoint replay passes for 12/12 v2 runs and rechecks every input-release and refusal receipt. Source hashes remain identical to the v2 preregistration. The standalone executable and fixed view/key contract differ from the production/golden runtime; no automatic promotion is justified.

## H / T / D / C / U

**H:** Under these local visible tasks, a bounded screenshot-relative controller with post-release confirmation reaches outbound and return goals more consistently than fixed action replay.

**T:** Three fresh pairs per domain, alternating order, fixed endpoint tolerances, finite action budget, retained first outcomes. V1 failures stay separate. No same-output overwrite is allowed.

**D:** V2 scoped local-task PASS: candidate 3/3 in each domain at the frozen image and GUI-state thresholds, with empty release. Stage-clear, model-in-loop benefit, production integration, and generic GUI performance remain UNTESTED.

**C:** Sparse samples, fixed horizontal orientation, known view ROI, repeated map geometry, unseeded native game timing, and template aliasing can invalidate extrapolation. More observation is not inherently better; native closed-loop completion is slower than replay here.

**U:** Native map scoring has integer-pixel resolution and no calibrated world-coordinate uncertainty. Screenshot timing brackets and GUI nearest-sample offsets remain in the evidence. There is no justified combined standard uncertainty, coverage factor, reliability distribution or general speedup from this block.

## Reproduction and retention

`unpack_sources.py` reconstructs the byte-identical executed sources from the hash-verified source archive. Then run `python decoded/verify_replay.py evidence` with the recorded NumPy/OpenCV versions. This launches no game and makes no model calls.

Git retention includes all scored structural endpoint masks with capture/hash receipts, all input admission/release receipts, offline refusal checks, and the selected independent GUI score samples. The full companion container archive also includes all RGB screenshots, all intermediate masks, complete controller/scorer streams, unsuccessful allocations and startup diagnostics. Do not relabel the smaller endpoint packet as the complete full-color trace.

For a **new** local development allocation, set `AI_SOURCE_ROOT` to the verified dependency checkout and `XAUTHORITY` to an empty file, then use `decoded/run_reanchor_v2.py NEW_OUT doom closed_loop NEW_PAIR_ID 0` or the GUI equivalent. Never reuse an existing result directory or describe a new run as the old first allocation.

The next useful experiment is to chain two independently verified native-view subgoals, including one door/view transition, with invalidation and recovery. It should test completion rather than add another long open-loop route or integrate predicted position indefinitely.
