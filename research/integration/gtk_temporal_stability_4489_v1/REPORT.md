# Issue #4466 — formal calibration result

## Result: PASS_NO_INPUT_STABILITY_GATE_CALIBRATED

One frozen OrbStack/Docker allocation ran once as `issue4466-gtk-pixel-stability-formal-01-20260926`. It is a scoped no-input pixel-stability calibration, not application-effect or task-success evidence.

### H / T / D / C / U

- **H:** In this GTK3/Xvfb fixture, same-window no-input redraw variation can be bounded by a frozen repeated-capture region mask while a distinct render-only decoy stays visibly distinguishable.
- **T:** 8 baseline captures, 8 more pre-decoy captures, and 16 post-decoy captures at 250 ms nominal intervals. All target captures use the original target XID; GTK Entry focus is set once as setup, with no key/button input. Independent live and offline audits run before and after process cleanup.
- **D:** PASS only for complete ordered/hash-verified evidence, fixed target identity and focus, distinct same-title/same-size non-overlapping decoy with nonzero pixel difference, 24/24 evaluation rows with no changed pixels outside the baseline mask, independent audit agreement, synthetic change detection, zero input/events/effect/model/provider calls, and clean process teardown.
- **C:** Local disposable GTK3/Xvfb fixture and pinned linux/arm64 OCI image; network disabled, read-only root, only `/out` writable. No model/provider, app save, or external service.
- **U:** Generalization beyond this fixture and cause of earlier deltas remain unknown. This does not establish GTK-wide behavior, application effects, adapter semantics, full #3240/#2606 acceptance, task success, or production readiness.

### Formal observations

- Captures: 32 ordered target XWDs (16 before and 16 after decoy); every raw file and its SHA-256 is retained in `evidence/formal-01.tar.gz`.
- Identity/focus: target XID `2097155`, PID `9`, title `AgentInterfaceGtkFixture`, geometry `(0,0,400,180)`; Entry focus XID `2097155` in all 32 before/after capture observations. Initial/after-decoy/final target identities agree.
- Decoy: XID `4194307`, PID `98`, same title and `400×180` dimensions, at `(450,20)` with no overlap; target and decoy XWDs differ at 13,026 pixels.
- Baseline: 8 captures; raw variable-pixel count 1,585, bbox `[20,20,379,53]`; the candidate's preregistered one-pixel halo is used for evaluation.
- Evaluation: 24/24 classified `STABLE_WITHIN_CALIBRATED_MASK`; changed pixels outside the mask `0`. Candidate and independent reconstruction match. Synthetic changed-pixel control detected.
- Input/effect: target events `0`; no effect file; input, model, provider, and target-operation counts are zero.
- Audits: live audit PASS before cleanup; independent offline audit PASS after cleanup; both have zero errors. Target and decoy terminated (`-15`), Xvfb exited `0`; formal container exited `0`, root read-only, network mode `none`.
- Formal image: `sha256:7c202113e519666007d7f6a74fa4a9854ed7cec62c07c1e80631474e69af7a27`, `linux/arm64`. Runtime source hashes and construction details are in `FREEZE.json` and `PREREGISTRATION.md`.

### Construction and STOP record

Construction 01 was HOLD because target and decoy overlapped: 72,000/72,000 target pixels changed. Construction 02 had a non-overlapping decoy but root focus, so it was insufficient for Entry-caret calibration. Constructions 03–05 refined Entry focus and audit separation; 05 predates final audit hardening and is not used as final-code validation. Construction 06 with the final scripts passed (32 captures, one focus context, 24 stable evaluations, zero events, matched independent audit and synthetic detection).

Infrastructure STOPs before formal: an apt-based image build stalled; a Dockerfile `FROM sha256:...` reference was treated as a registry name; BuildKit failed resolving local image metadata with HTTP 502; container-to-container `docker cp` is unsupported. No formal allocation was performed during those failures. The final image was assembled from the exact pinned local base by creating a named staging container, copying frozen runtime files from host, and committing that container; it is not represented as a Dockerfile build. No retry or tuning occurred after the formal invocation.

### Reproduction / integration

Read `PREREGISTRATION.md` first. `evidence/formal-01.tar.gz` contains the raw allocation directory including `manifest.json`, `captures.jsonl`, all XWDs, candidate decisions, live/offline audits, event logs, and cleanup receipts. The scripts beside this report and the image ID in `FREEZE.json` are the frozen runtime. The tarball's SHA-256 is in `SHA256SUMS`. Construction and synthetic rows are not formal live evidence.

This successor preserves the HOLD in #3240 / PR #4464 unchanged. It calibrates only no-input temporal stability for this fixture; it does not satisfy the parent issue's broader app-effect acceptance.

## Parallel-work integration note

During integration, the independent #4466 occlusion/capture-validity study was found merged as PR #4478. That result establishes all-black XWD on an overlapping decoy, a distinct finding from this allocation's non-overlapping decoy and focus-context temporal mask. The allocations are complementary, not interchangeable. Because #4478 already owns `gtk_pixel_stability_4466_v1/`, this unchanged formal bundle is retained under the separate additive path `research/integration/gtk_temporal_stability_4489_v1/`, tracked by successor Issue #4489. The colliding PR #4486 was closed without merge; no formal rerun or evidence rewrite occurred.
