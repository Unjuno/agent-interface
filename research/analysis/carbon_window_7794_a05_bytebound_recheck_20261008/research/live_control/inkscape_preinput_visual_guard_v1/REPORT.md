# Inkscape pre-input visual selection guard under paint lag

Decision: **REJECT_VISUAL_SELECTION_GUARD**. A just-in-time screenshot guard over the expected A selection handles did not fail closed when Inkscape's semantic selection had already changed to B. In every switch case the guard still saw the exact A-handle counts and admitted the same Right×5 input, which persisted a B movement.

Task `INKSCAPE-PREINPUT-VISUAL-GUARD-20260916-015`, Issue #327. Publication base `871ece721f5aed021428d50668f24f055acf748d`. Zero model/game calls. No shared runtime/workflow/scorer mutation.

## Why this rung exists

Issue #321 / merged PR #324 showed an ordinary real Inkscape race: after A was selected and a final screenshot was taken, changing selection to B before Right×5 redirected the persisted SVG effect to B. A posthoc correction then found that the original blue-pixel selection gate was not selection-specific; actual black A handles were visible in 16/20 retained frames. The persisted effect result stayed unchanged.

The smallest proposed repair was one additional observable selection check immediately before input. This rung tests that repair directly; it does not claim another screenshot can create atomicity.

## Retained predecessor failure 014

`INKSCAPE-PREINPUT-VISUAL-GUARD-20260916-014` froze the same guard thresholds but inherited a weak initial selection acquisition. Seven first cases completed (stable 3, switch 4); every completed switch case false-admitted and moved B. The next scheduled stable case failed before effect because A-selection revalidation was absent. 014 is retained as `STOPPED_SETUP_FAILURE`; it is not resumed, pooled, or counted below.

015 changes setup only: after F1/Escape and one Tab, wait up to 10×50 ms setup-only screenshots until **actual black A selection handles** are visible. No extra Tab is issued. The final revalidation then independently requires the same black handles before entering the unchanged race.

## Frozen candidate

At the frozen 120 ms post-revalidation boundary, capture one small fixed ROI around A (25,810 pixels). Count dark handle pixels on A's top, right, and bottom strips; the left side is excluded because Inkscape ruler/chrome contaminates it. Require `top>=30`, `right>=80`, `bottom>=30`.

- if the invariant fails or capture is unavailable: `DEPENDENCY_UNAVAILABLE`, no Right input;
- if it passes: admit Right×5, save, then score persisted A/B SVG positions.

Ten stable + ten switch fresh Inkscape/Xvfb processes were frozen before measurement. Switch changes A→B immediately after final A revalidation; no semantic screenshot occurs until the guard itself.

Frozen source identities:

- `run_case.py` SHA-256 `b0ee64cb050422221451161d0e067f38885d55cfb54558826585fa24cb05b936`
- `audit.py` `6fdc132c18501566179c8f2fa17e436beb456fca71ff345b4140f521a7a453b5`
- `schedule_015.json` `ff2395a6df1966970965e4fad66e511f942a9273e16473a1cab39f06564ba887`
- `prereg_015.json` `462f2b0c3a35162cb64fb739c531739b710d55432bcc20b6fa99c66a8c7d3064`

## First measured result

| context | n | guard verdict | persisted effect | correctness |
|---|---:|---|---|---|
| stable A | 10 | ADMIT 10/10 | A +10, B 0 in 10/10 | **10/10 correct** |
| switched A→B | 10 | **ADMIT 10/10** | A 0, **B +10** in 10/10 | **0/10 correct; 10 false admits** |

All twenty final A revalidation frames contained the real black A handles before the race began. All twenty cases ended with relevant keys and mouse buttons empty. Setup acquisition required exactly two setup-only samples in every case.

Most importantly, **the guard observation itself was identical across semantic contexts**: all 20 guard captures reported `top=64`, `right=176`, `bottom=64`. Yet switch cases immediately afterward applied Right×5 to B. Thus this candidate cannot distinguish current semantic selection inside the tested window.

Frozen independent audit: `REJECT_VISUAL_SELECTION_GUARD`, integrity pass `True`; counts `{"release_ok": 20, "revalidation_ok": 20, "stable": 10, "stable_admit_correct": 10, "switch": 10, "switch_false_admit": 10, "switch_stopped": 0}`. Five corruption controls were rejected.

## Cost (descriptive only)

Guard ROI capture wall time:

- stable median 5.093 ms, range 4.621-15.220 ms;
- switch median 6.079 ms, range 4.367-19.261 ms.

No speed claim follows. A cheap check that reads the wrong/stale semantic projection is not useful merely because it is fast.

## Environment / provenance correction

Actual 015 runtime: CPython 3.13.5, Linux 6.18.44, Inkscape 1.4, Pillow 12.3.0, Intel Xeon Platinum 8573C, affinity CPUs 0..4, frequency unpinned. The imported Xlib module path in this container reports version tuple `(0, 15)`. A retained 0.33 wheel exists from earlier setup work, but 015 did **not** run with a PYTHONPATH override, so this report does not claim 0.33 for 015.

## Why the guard failed

Construction and measured cases show a separation between **semantic selection** and **painted selection affordance**. The Tab event changes which object receives Right input, but the immediately sampled selection-handle pixels can still depict A. A later full-frame construction probe eventually paints B handles and the X toolbar value `220`, confirming that the information becomes observable later; it was not reliably current at the frozen effect boundary.

Therefore screenshot freshness at capture time is not sufficient evidence that the screenshoted UI affordance reflects the latest internal application context. This is a different problem from stale screenshot identity; it is application paint/publication lag.

## H / T / D / C / U

**H.** A just-in-time A-selection visual guard might reject post-revalidation context changes.

**T.** Twenty frozen first live-Inkscape cases after bounded setup acquisition, same 120 ms race and Right×5 effect. Candidate changes only one pre-input visual guard.

**D.** **REJECT_VISUAL_SELECTION_GUARD.** Stable availability/correctness was 10/10, but switch false admission was 10/10. Do not tune thresholds or shrink the poll interval to rescue this exact candidate.

**C.** A different public source (for example a reliable accessibility selection identity) could publish semantic selection sooner than rendered handles. Conversely, another application may paint synchronously enough for a visual guard to work.

**U.** One Inkscape version/action/X11 host and an evaluator-induced Tab race. This does not estimate natural race frequency. The guard-after-capture interval still exists even if a future observation source is fresher.

## Next single question

Do not add more screenshots. Determine whether a **non-privileged public semantic source** already available to ordinary desktop control (e.g. accessibility state) exposes current Inkscape selection identity with enough freshness to distinguish A from B at the same boundary. If no such source exists or cannot be bound to the target, retain `DEPENDENCY_UNAVAILABLE`; do not invent atomicity or add an app-specific effect API.
