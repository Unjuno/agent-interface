# Real Inkscape selection-context race after final visual revalidation

Decision: **PASS_REAL_APP_CONTEXT_RACE** at the tested scope. In real Inkscape 1.4, ordinary X11 keyboard input was interpreted against the selection current at event time. After A was visually revalidated as selected, switching selection to B before the same `Right` x5 input redirected the persisted SVG effect to B in 10/10 fresh cases rather than rejecting the stale A-bound intent.

Task: `INKSCAPE-CONTEXT-RACE-20260916-013`, Issue #321. Publication base `d24dbc3a47c6a3b317a4cef788f8301b791880d9`. No shared runtime/workflow/scorer/history file was modified by the experiment. Zero model and game calls.

## One-factor question

Both arms start from a fresh two-object SVG (`A` x=50, `B` x=220), Inkscape's Select tool, and standard Tab object traversal. A is selected, then a fresh screenshot must show:

- A and B pure-red centers within ±5 screen pixels of their initial locations; and
- the current-theme blue A selection marker in a fixed A-bound strip (>=100 pixels; all measured cases observed 276).

That screenshot is the **final visual revalidation**. After it:

- `stable`: no selection change;
- `switch`: exactly one Tab changes selection from A to B.

Both arms then reach the same 120 ms post-revalidation boundary, receive no intervening screenshot/semantic observation, inject exactly five ordinary `Right` key presses, save with Ctrl+S, and are independently scored from the persisted SVG. Therefore the changed factor is the post-revalidation selection context.

## Frozen design

The pre-measurement freeze is in Issue #321. Ten matched pairs / 20 fresh Inkscape+Xvfb processes; order alternates stable/switch then switch/stable by pair. Frozen source hashes:

- `run_case.py` `02da64b8a18de7605e767fff00a7abfaf6e72a9c44646bdcf38c8ebcc69690b3`
- `audit.py` `94fc84c94c8f41f68ab9ce058edf0ac3f85d259da2700c3e06e6930c40da02bb`
- `schedule.json` `af20a51b72ea18a7422d06f95d83dc95f150f88f18b0fea3897dd248d9dfc5af`
- `prereg.json` `ee0f01b4f1183ef14c0e7104fce74570b421fa23b5e8e95c578ac12c6bc19edc`

Retained offline dependency hashes are in Issue #321.

## Preparation failures before measurement

No measured case was run until construction passed. Preserved preparation record includes: omitted `six` dependency for python-xlib 0.33; a screenshot workspace x-bound that clipped A; unreliable pointer-click object selection; and a legacy black-handle selection scorer that did not match the current Inkscape theme. The final construction used F1/Tab and current-theme blue selection-marker evidence. Raw bytes for all early failed construction attempts were not all retained because construction directories were overwritten before freeze; the exact failure sequence is therefore narrative evidence, not a complete raw archive. Final excluded construction is retained.

## First measured result

| Arm | n | Persisted A effect | Persisted B effect | Result |
|---|---:|---:|---:|---|
| stable | 10 | **+10 in 10/10** | 0 in 10/10 | intended A effect |
| switch A→B | 10 | **0 in 10/10** | **+10 in 10/10** | wrong-target relative to revalidated A intent |

Hard gates:

- stable correctness: **10/10**;
- switch wrong-target effect: **10/10**;
- A final visual revalidation: **20/20**;
- relevant keys and mouse buttons empty after save: **20/20**.

The application did **not** reject the stale intent. XTEST delivered the requested Right key sequence correctly; Inkscape applied it to B because B was the current selection when the events arrived.

This is an application-level effect result, not merely an input receipt: the independent endpoint is the saved SVG (`A.x` / `B.x`) after Ctrl+S.

## Descriptive timing, not a speed claim

The measured post-revalidation phase-to-effect-start interval was intentionally matched:

- stable median 120.481 ms, range 120.306-120.807 ms;
- switch median 120.695 ms, range 120.163-121.047 ms.

The ~120 ms window is a frozen experimental race window, not a human/UI latency claim. No performance comparison is promoted.

## Environment

- Inkscape: Inkscape 1.4 (e7c3feb100, 2024-10-09)
- CPython 3.13.5; Pillow 12.3.0; python-xlib 0.33 retained wheel
- Linux 6.18.44; CPU INTEL(R) XEON(R) PLATINUM 8573C; process affinity [0, 1, 2, 3, 4]; CPU frequency not pinned
- private Xvfb 1280x800x24 + Openbox per case
- real XTEST F1/Tab/Right/Ctrl+S events

## ERROR CHECK

Frozen independent audit reports `passed=true` with counts {"release_ok": 20, "revalidation_ok": 20, "stable": 10, "stable_correct": 10, "switch": 10, "switch_wrong_target": 10}. Five post-measurement corruption controls are all rejected: stable wrong target, switch no longer wrong target, missing revalidation, key-left-down, and missing case. These controls add no live samples.

Audit SHA-256: `98d902e8fc0973e879e85f806dc2534d3ba604b4e13b59c6a7b7d0670a62745a`.

## H / T / D / C / U

**H.** Ordinary Inkscape keyboard input is resolved against the current selection at event time; a context change after final revalidation can redirect a valid key sequence rather than be rejected.

**T.** Twenty frozen first live-X11 cases, 10 matched pairs, fresh Inkscape process and SVG per case, final visual A-selection revalidation, same 120 ms budget, same Right x5 and save, independent saved-SVG scorer. No model/game calls.

**D.** All frozen gates pass: **PASS_REAL_APP_CONTEXT_RACE**. This transfers the synthetic #273 boundary to an ordinary real application path.

**C.** The selection change is an evaluator intervention and deliberately uses Tab traversal; a natural user/window race may have different timing. Other Inkscape actions or other applications may themselves disable/reject stale inputs.

**U.** One application/version, one keyboard action, one X11 backend, one host family, small deterministic fixture. There is no authoritative app incarnation token on the universal input path and no proof about Windows/macOS. The result demonstrates a race, not its production incidence rate.

## Architectural consequence / next single question

A final screenshot revalidation cannot by itself supply atomic semantic binding to a later generic OS input. In this real app, a context change during the check-to-effect window redirected the effect 10/10.

The next high-information experiment should not make the race window smaller by repeated polling. Test one **fail-closed context guard** available without privileged application semantics: after final revalidation and immediately before input, verify a cheap observable selection-context invariant; if the invariant is unavailable, return `DEPENDENCY_UNAVAILABLE` rather than claiming atomicity. Compare only guard availability/correctness, not task speed.

## GitHub retention boundary

GitHub retains the frozen study source, preregistration, schedule, preparation-failure record, REPORT, aggregate per-case RESULTS, audit/environment/corruption controls embedded in RESULTS, saved SVG bytes, and SHA-256/byte counts for all 40 measured PNG captures.

The exact full local archive contains 119 retained files and is attached to the conversation as `inkscape_context_race_v1_complete.tar.xz`:

- bytes: 1348360
- SHA-256: `7184ed8a643a1ceb8d32cbbb0c9ba56cfa38f19db885549326dcaf7491dc2649`

The 40 PNG capture bytes are **not claimed GitHub-retained**. Their exact SHA-256 values are in `RESULTS.json`. This boundary does not affect the persisted-SVG effect endpoint, whose exact bytes/text are retained in RESULTS, but independent recomputation of the visual selection-marker pixel count requires the full local archive.

Fresh extraction of the full archive reproduced the frozen audit object byte-for-byte (audit stdout SHA-256 `98d902e8fc0973e879e85f806dc2534d3ba604b4e13b59c6a7b7d0670a62745a`).
