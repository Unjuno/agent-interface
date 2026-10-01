# Issue #3983: composite capture coherence

## Status

Local result: **PASS_COMPOSITE_CAPTURE_COHERENCE_SCOPED**.
Sequential capture under the one-spatial-snapshot requirement: **FAIL_MIXED_CAPTURE_PRESENTATION**.
Delivery/integration: **HOLD / STOP_SOURCE_PUBLICATION_TOOL_SAFETY_CHECK**.

GitHub MCP rejected publication of the new composer source. The branch therefore contains only non-executable evidence, not a complete reproducible source bundle. Do not merge/adopt this Draft as a completed runtime or research-source delivery. The rejected source and binaries are not hidden in the raw-data package. No shared runtime changed. Earlier #3951 and its publication STOP are separate and unchanged.

## Origin, ownership and roadmap

Parents: #8/#570's same-source composite representation; closed #1968's multi-resolution serialization study. #1968's actual retained disposition is HOLD_NO_FORMAL_CONTAINER, not a formal PASS. Preserve it and PR #1983; this is neither its rerun nor closure of #2031/#3204.

Intake main: b2457b746a6df06f6536585dfe2ab937aff639f4. README, CURRENT_GOAL, ROADMAP, open/closed Issue searches, open PRs and branch inventory were inspected through GitHub MCP. The proposed composite namespace had no matching branch. Parallel XDamage, cue sampling, passive reader, epoch and source-content work was excluded.

Publication branch: research/issue-3983-composite-capture-coherence-v1, created from main 03ac3306861c2692b796bb14e2880ba9829d8291. Its 46-commit advance from intake comprised other additive research paths; this experiment imports no changed repository runtime. Owned namespace: research/observation_gating/composite_capture_coherence_v1/ only.

Completed locally: intake -> construction with retained STOP -> exact preformal hash freeze/readback -> one live 24-case allocation -> separate raw audit and corruption controls -> result/data retention.
Remaining: authorized complete-source delivery -> reproducibility review -> PR checks/main integration. Keep the Issue open, PR Draft and owned branch retained. No unrelated branch was deleted. The repository-wide ROADMAP and #2789 remain open.

## H: hypothesis and analytical argument

Sequential captures of two spatial regions can describe different completed display states despite unchanged window identity and geometry. Both panels derived from one immutable captured frame preserve that source's spatial state even when the live window updates during composition. This does not make the old capture current.

The declared fixture has two identical corresponding non-flat regions in each completed state. In state A both regions are blue/white; in B both are amber/black. If the first region is captured in A and the second after the update to B, the composed blue/amber image is neither committed state. If both regions are cropped from the retained A frame, each local crop reads the same immutable bytes, so both remain A regardless of the subsequent live update. A later endpoint B then proves that this coherent composite is not the current endpoint. These conclusions depend on the fixture's completed-state and immutable-source assumptions, not on an arbitrary desktop atomicity guarantee.

Xlib's primary specification defines XCopyArea for copying between drawables and XGetImage for reading a drawable rectangle. It also documents visibility/backing-store restrictions and that the pointer cursor is not included. This experiment uses an unobscured owned software drawable; the specification is not evidence that arbitrary GPU/compositor captures are atomic.

Reference: https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html (Copying Areas; Images).

## T: frozen experiment and implementation assumptions

Allocation: composite-capture-coherence-20260922-01. Formal invocations 1; retries/replacements/tuning 0. Twenty-four fresh renderer/observer pairs, grouped into three private Xvfb lifetimes: two policies, four update schedules and three repetitions, with reversed policy order in the middle repetition. Twelve matched comparisons are not 24 independent randomized trials.

Each native renderer prebuilds two 128x32 pixmaps and publishes a complete state with one XCopyArea request. Panel rectangles are (8,8,16,16) and (88,8,16,16). Explicit pipe acknowledgements and XSync choose the schedule; no sleeps choose the interleaving. A separate native observer uses XGetImage and XGetPixel to retain exact normalized RGB bytes, native format metadata and monotonic capture brackets. Separate pre/post full captures are scoring-only.

SEQUENTIAL_ROI performs two region captures. ONE_FRAME_CROPS performs one full capture and two local crops. UPDATE_BETWEEN occurs after the first ROI or after the full capture and before the second local crop, respectively. Both paths retain a 32x16 composite RGB raster and per-panel capture provenance. All packages explicitly have input authority false and current-at-delivery unknown. The research composer operates on trusted internally generated panels; no hostile metadata/authentication validator is certified.

Actual environment: supplied Linux 6.18.44 x86_64/glibc 2.41 container; CPython 3.13.5; gcc Debian 14.2.0-19; depth-24 TrueColor, native 32-bit pixels with row stride four times capture width, RGB masks 0xff0000/0xff00/0xff. Xvfb uses displayfd, a newly created socket, 320x120x24 and TCP disabled. No inherited desktop attachment, keyboard/mouse emission, model/provider or network request, package installation, Docker restart or shared runtime mutation. Docker CLI and image identity were unavailable: not Docker Desktop/OrbStack replication. CPU frequency and physical isolation were not measured; no timing benchmark is claimed.

Clock records use CLOCK_MONOTONIC/time.monotonic_ns and are diagnostic ordering evidence. Byte accounting uses three octets per normalized RGB pixel; the 32x16 output has 1,536 bytes. The sequential acquisitions total 1,536 RGB bytes; the full-frame acquisition has 12,288. Both byte quantities use the same representation. This is an 8x source-byte difference, not a measured transport, token, latency or end-to-end cost ratio.

Preformal manifest: commit 727e9cf4532e4d42a49515304a88e6e4d9ee5e8e, blob 9f12b9c38212e71ae79050ca3b6a2b8b96d6e67b. FREEZE SHA256 a1d1b46e046f396f3644cc76fef74b2fd5606eaab8e5ff8e53c676abb687c4fb. Issue freeze comment 5766639342 preceded formal execution. The historical formal_started=false field records that preformal instant; it is not the current status.

## D: complete first outcome

| Update schedule | Cases per policy | Sequential coherent | One-frame coherent | Sequential matches final | One-frame matches final |
|---|---:|---:|---:|---:|---:|
| STABLE_A | 3 | 3 | 3 | 3 | 3 |
| UPDATE_BEFORE | 3 | 3 | 3 | 3 | 3 |
| UPDATE_BETWEEN | 3 | 0 | 3 | 0 | 0 |
| UPDATE_AFTER | 3 | 3 | 3 | 0 | 0 |

All 24 planned cases completed with exact source/crop/composite/identity/order reconciliation. All 48 renderer/observer processes exited 0. All three Xvfb processes exited 0 and their sockets disappeared; every terminal window count was zero and key/button state neutral. Formal and audit command exits were observed 0, with empty stderr. All eight source hashes remained unchanged; actual executable/library identities were checked before invocation.

Separate raw-only audit: PASS_RAW_AUDIT, errors empty. It imports neither runner nor composer and independently reconstructs the reference pixel patterns, schedule, source/crop/composite bytes, clock brackets, geometry, identities, process/cleanup outcomes and complete denominator. This is a separately implemented auditor/process, not an external human review.

Thirteen corruption controls all rejected: missing/duplicate case; native pixel; source index; composite pixel; panel pixel/coordinate; authority flag; Boolean exit; missing server exit; future panel clock; geometry; Boolean repetition. They cover a finite test set, not arbitrary auditor soundness. Whole-file hashes additionally detect accidental byte changes.

Raw: formal-01/RAW.json, 3,352,631 bytes, SHA256 e5f0aea94203035be3ed52fd589b8f008b16d1a86dc2ffea98b48768fd5e8e56.
Audit: AUDIT.json, SHA256 0a80cbd946d0b2c7b306d711757dc4c08e28717778eb6a08b9d9dfa4bd790006.

The sequential result violates the declared same-state presentation requirement. Sequential panels are not inherently erroneous when separately labeled as different-time observations; neither tested package granted action authority. No production runtime defect is asserted.

## Retained construction failures and publication STOP

Construction-01: the new Xvfb selected unused :0, but the harness incorrectly treated equality with inherited DISPLAY=:0 as an existing-desktop collision. It stopped before renderer/case execution, and its server exited 0. The old auditor also raised FileNotFoundError for the correctly absent empty journal. Original source, raw and tracebacks remain local; no formal result was consumed.

Preformal correction: require the socket not to exist before the owned Xvfb starts and require that child to remain alive; report incomplete journal as incomplete evidence rather than crashing. Construction-02 completed 8 excluded cases and 12 corruption controls. A final preformal addition retained the actual composite raster; construction-03 completed 8 excluded cases, 10 unit methods and 13 corruption controls. Both earlier source snapshots match their original raw hash inventories; no construction row enters formal results.

The new compose.py create_file request was rejected by the GitHub MCP safety check. No successful source commit was returned. The formal source remains locally frozen but unavailable on the branch; data-only publication does not cure this delivery limitation. No alternate source upload or source-containing archive is supplied.

Initial audit-receipt transfer at commit 3fab0813be62dbe8a35f7b4a43b19baf12b984ac contained an invalid Base64 copy (blob f809515bbc14a7926b2020cfe5476c642acb9aaa). Readback detected the mismatch. Storage-only correction 71e8a13f74e283b6d408905a7aedbea37bdf4627 restores exact blob 7b0c0d6303f048dbdf6928b6b35ad0ba356d1e16. Both original formal raw-data parts matched their declared Git blobs on first readback. Local lossless decoding reproduces the original raw and audit hashes exactly; no experiment or auditor was rerun for this storage check. The failed transfer remains in branch history.

## C: competing explanations

The barriers deliberately expose a temporal mismatch; this is not an estimate of natural race frequency. Identical per-state panels simplify exact scoring and do not establish model localization. Single-copy software-X11 drawing and separate observer synchronization are stronger conditions than general toolkit/GPU/compositor behavior. More source bytes may eliminate an advantage even though coherence is preserved. Hashes provide content integrity, not authentic producer binding. Geometry equality is a control, not a complete target identity proof.

## U: transfer limits and integration handoff

No model usefulness, task completion, token saving, speedup, physical scanout, cross-platform atomicity, arbitrary app snapshot consistency, authentication, multi-window transaction or production input safety is established. No statistical confidence interval or combined metrological uncertainty is assigned to these barrier-selected Boolean/byte outcomes; no population parameter is estimated. Dominant uncertainty is model/backend/application transfer, not floating-point arithmetic.

For #2789's observation boundary, retain one source-capture identity and exact source rectangle per panel. Do not replace capture time by composition time. Preserve mixed-time panels as such rather than claiming a coherent snapshot; verify currentness separately before input. These are supported design constraints, not an integrated desktop acceptance.

Related transfer domains: computer vision needs consistent feature context; distributed snapshot design separates common provenance from simultaneous state; human-computer interfaces need explicit historical/current presentation. Applications in these domains require their own source and freshness contracts.

## Data-only review

RAW_DATA.json documents a lossless XZ/Base64 encoding of the exact formal RAW.json. Concatenate its parts in declared order, decode Base64, then decompress XZ and verify raw length/SHA256. This produces data only and executes no fixture or auditor. The branch does not contain the rejected experimental sources, so this is not a complete reproducibility recipe.

AUDIT.json.gz.b64 losslessly encodes the original audit JSON using Base64 over gzip; its decoded hash is the AUDIT.json hash above.

A separate conversation ZIP retains 41 original non-executable evidence files, including the full journal, construction STOP/results, exact stdout/stderr, execution receipts, environment and hashes. Neither distribution includes Python/C sources or the native binary. Keep this publication Draft.
