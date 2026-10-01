# Issue #4466 — one-shot GTK pixel-stability calibration

Allocation: `issue4466-gtk-pixel-stability-formal-01-20260926`

## H / T / D / C / U

**H — Hypothesis.** For this local GTK3/Xvfb fixture with the GTK Entry held in one observed focus context, temporal redraw variation is confined to a baseline-derived pixel region. A frozen region gate can classify all subsequent no-input captures as stable while a same-title/same-size decoy on a distinct, non-overlapping XID/PID remains independently pixel-distinct.

**T — Test.** Run the frozen scripts once in the frozen linux/arm64 image. Capture 8 baseline frames and 8 further frames before a render-only decoy; then capture 16 frames after decoy creation, every 250 ms. Capture the original target XID, retain every raw XWD, hash, window geometry/title/PID/focus observation before and after each capture, event log, and cleanup receipts. Set GTK Entry focus once before sampling using XSetInputFocus; send no key/button input. The candidate calibrates a one-pixel halo around pixels that vary among the first eight frames and classifies the following 24 frames. A separate auditor independently parses the bytes and recomputes the decisions. Live audit runs before cleanup; offline audit repeats after cleanup.

**D — Decision.** PASS only when all 32 ordered rows and raw hashes reproduce; the target window identity and Entry focus remain fixed; decoy XID/PID differs, geometry/title match, windows do not overlap, and decoy pixels differ; all 24 evaluation captures have zero changed pixels outside the frozen mask; independent/candidate decisions match; the synthetic changed-pixel control is caught; no input, event, effect, or model/provider call occurs; and post-cleanup process receipts plus offline audit pass. Any evidence/discrimination mismatch is HOLD; construction/provenance/infrastructure failure is STOP. This calibrates only this static GTK/Xvfb no-input gate.

**C — Controls and constraints.** Only the repository-derived disposable GTK fixture, a second same-title/same-size decoy window, local Xvfb, and the exact pinned OCI image are used. `--network none`, read-only container root, a read-only source mount during construction, and only `/out` writable. No app save, injected input, model/provider, or external service. Construction allocations remain separate from the one formal allocation; predecessor #3240/#4464 evidence is untouched.

**U — Unknowns.** The cause of earlier target-pixel deltas (caret, focus, redraw, timing, or other); transfer to other GTK apps, window managers, display scales, or real desktops; and any application-effect, adapter, integrated #3240/#2606, task-success, latency, or product-level claim remain unknown.

## Frozen schedule and gates

- Xvfb: 1000×500×24, TCP disabled; target and decoy: 400×180, same title.
- Target at (0,0); decoy at (450,20), so the windows do not overlap.
- 32 target captures total: 8 calibration + 8 pre-decoy evaluation + 16 post-decoy evaluation; 250 ms nominal spacing within each phase.
- Focus must equal the target GTK Entry XID at every before/after observation.
- A single invocation. No retry, tuning, or source/image modification after freeze.
- Required outcomes and stop conditions are as stated in D; synthetic controls are not live evidence.

## Source and image construction

Runtime files are the adjacent `runner.py`, `fixture.py`, `decoy.py`, `stability_gate.py`, `xwd_pixels.py`, `audit.py`, and `case_schedule.json`. Freeze their SHA-256 values in `FREEZE.json` before formal execution. The base is `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, with `/usr/bin/xwd` copied from pinned `agent-interface-map01-clock-control-v1@sha256:05e01176ffcc2258ca88d7f8aafb6bd9e3915cd7ad19af196924008ff16f84b6`; the resulting local base ID is `sha256:296d358f5c71e6c3e766c49ebfe13b9b1ec5c2837157da2cfe406ee73bfb2992` (`linux/arm64`). Freeze the final derived image ID and platform in `FREEZE.json`.

The final experiment image is staged by creating a named container from the exact base image, copying this frozen directory into `/experiment`, then committing that container to an immutable local image. This was chosen because Docker BuildKit could not resolve local image references without registry access. It is an OCI image snapshot, not a claim of a successful Dockerfile build. The broken exploratory Dockerfile is not part of the formal runtime.

## Construction history (not formal results)

- Construction 01: HOLD. Target and decoy overlapped at (0,0); 72,000/72,000 target pixels changed. This exposed occlusion and was corrected before freeze.
- Construction 02: limited PASS. Non-overlapping decoy worked, but focus remained the X root; it did not exercise the Entry caret context.
- Constructions 03–05: progressively added Entry focus and independent candidate/auditor checks. Construction 05 predates the final audit hardening and is not relied on as final-code verification.
- Construction 06: latest-code PASS in the pinned base image; 32 rows, one focus XID, zero events, 24 stable evaluations, candidate/auditor agreement, synthetic change detected, live and post-cleanup audits.
- Infrastructure STOPs: an apt-based image build stalled; a `FROM sha256:...` Dockerfile reference was interpreted as a registry image; BuildKit local-image metadata resolution returned HTTP 502; container-to-container `docker cp` is unsupported. These were construction failures only. The documented local container-stage/copy/commit procedure produced the pinned base; no formal allocation occurred in these attempts.
