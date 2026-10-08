# Inkscape click-to-key boundary: fixed probe and primary use

2026-09-20. The previous native Inkscape transfer completed a rightward move but
18 Right chords moved x=50 to 84. This follow-up separates the wait after click
from the wait before save, using the existing shared bridge and wait_update.
There is no new runtime primitive or default delay.

## Allocation and observations

The allocation was written before input: counts 1 and 18, after-click wait 0 or
50 ms, before-save wait 0 or 50 ms, two blocks. Block two reverses condition order.
Every case starts a fresh private X11 session and Inkscape profile (seed 991086).
The initial full PNG must exactly match the previously primary-viewed reference
before admitting the fixed point (600,378). A mismatch retains failure without
input. All sixteen initial images matched. Saved SVG scoring occurs only after
all declared input; there are no adaptive retries or discarded rows.

The official [Inkscape keyboard reference](https://inkscape.org/my/doc/keys.html)
documents the default two SVG pixel nudge. The expected x is therefore 50+2*N,
with y=50, width=40, height=30 and no transform; this is not screen displacement.

| After-click wait | Exact saved geometry | Allocation |
| --- | ---: | ---: |
| 0 ms | 4 | 8 |
| 50 ms | 8 | 8 |

Failures were cases 0, 1, 10 and 14. Single-key failures left x=50; case 10
(18 chords) saved x=84 instead of 86. Waiting only before save did not eliminate
the failures. The same no-wait 18-key condition also succeeded in this allocation:
loss is intermittent, and the internal cause or identity of a missed key is not
established. These are descriptive counts, not a general reliability estimate.

## Actual primary-assistant use

Separately from the automated probe, the primary assistant opened a fresh
Inkscape session (seed 991087), viewed source 1, grounded the same corner, and
submitted one guarded click, wait_update 50 ms, seven Right chords, Ctrl+s and
wait_update 300 ms through agent_exchange --native --review compact.
Seven was not a count in the preceding allocation.

The source-7 image displayed x=64, y=50, width=40, height=30 and a saved title.
The large tool response was truncated at a context boundary; the same immutable
reply was presented again read-only, without submitting another action.
After viewing it, explicit finish returned the independent SVG score, also x=64
with unchanged y/size and no transform. One native program, verified neutral
release. The actual client metadata is retained without base64 in client-1.json;
see SUMMARY.json for local exchange timing, which excludes host/model time.
There was a long review-to-finish interval; this is not a live human-speed result.

## Integration decision and limits

For this tested Inkscape recipe, use an explicit short wait between selecting a
shape and dependent keyboard input. Keep it caller-selected. This small fixed
comparison supports that recipe, not an automatic global delay, a minimum
sufficient delay, a new readiness signal or a guarantee across loads/versions.
Do not replace the returned image and independent task effect with title matching.

Probe and self-use each preserve original results, images, programs, saved SVG
and terminal process cleanup. Return code -15 is intentional teardown and code 1
also occurs for the window manager; terminal status is not clean app-exit proof.
archive-and-audit.py independently checked all sixteen saved SVGs, case coverage,
release rows, cleanup, decision/reply hashes and observation-to-PNG hash links.
Original absolute paths remain provenance; use archived images by filename.
The probe's reference-source argument expects its artifact path to exist.
The first archive audit stopped on the reference image's original filename:
it had been archived as reference.png. Adding that explicit filename mapping
resolved the audit; no experiment or input was rerun. The final audit checked
163 image hash links.

Source snapshots are the exact executed versions; all other dependencies are
identified by base f54105e5b4f25e04d7e98caf44d57542bfdbc661. No common runtime code
changed. SHA256.json covers every retained file except itself.
Model tokens/cost are unavailable; helper model calls were zero. This is not the
formal GTK receipt matrix, a mixed-app session, crash recovery or a frozen golden
benchmark. Issues #2704 and #2706 remain outside this evidence.
