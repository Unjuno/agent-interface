# OpenTTD bounded finish and paired sign view, v1

## Bounded-limit finish repair

The frozen v6 model allocation exposed a deterministic race: after applying the
twelfth proposal, driver v4 raised from its loop `else` while the supervisor was
still reading `applied-12.json` and preparing `abort.json`. The independent
finish command therefore never ran.

`timing_envelope_openttd_l_driver_v5.py` keeps the twelve-proposal limit but
waits up to30 seconds for the supervisor's explicit finish message. It then
sends one `finish-once` request, records the independent evaluation and exits.
It does not infer success from reaching the limit.

The frozen model-free integration probe sends twelve observe-only proposals and
then the same bounded-limit abort used by the supervisor. It passes with:

- zero model calls and zero pointer steps;
- 50 durable calls and39 runtime observations;
- independent `bounded_turn_limit` failure after12 applied proposals;
- unchanged target, forbidden, surrounding-road and save state;
- verified input release and process exit0;
- matching Windows and WSL audits.

This repairs evidence retention. It does not improve task performance.

## Paired sign presentation feasibility

The OpenTTD manual documents Ctrl+1 as the station-sign transparency control and
also lists general sign display as a separate display option. Two preregistered,
zero-model probes apply the already verified tree-transparency transition and
then Ctrl+1:

1. seed991003 five-tile L geometry;
2. held-out seed991002 straight-road geometry.

In both fixtures the custom A/B/C/X sign background changes while independent
task state and the byte-pinned save remain unchanged. Full-frame differences are
166,104/1,024,000 and186,377/1,024,000 pixels. Those counts include normal game
progress between captures and must not be interpreted as isolated sign-effect
size. The probes establish availability and second-geometry transfer only.

The first launch command accidentally used Windows Python and failed on the
Linux-only `fcntl` import before app launch or input. The traceback is retained;
the fixed preregistration was then executed in its declared WSL/Linux setting.

Keep the sign transform as an unpromoted paired-observation candidate. The next
allocation must pause or otherwise match dynamic state, measure only the label
presentation delta, and compare actual model targeting plus independent task
correctness. A changed screenshot alone is not evidence of better grounding,
lower token use or faster operation.

Official sources:

- https://wiki.openttd.org/en/Manual/Transparency%20options
- https://wiki.openttd.org/en/Manual/Hotkeys
