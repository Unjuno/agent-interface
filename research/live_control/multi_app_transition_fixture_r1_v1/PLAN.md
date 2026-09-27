# Mixed-app finite transition fixture — R1

Task: `MULTI-APP-TRANSITION-LIVE-FIXTURE-R1-20260918-001`

H: one private-X11 session can reproducibly expose Chromium geometry drift, cross-app focus drift to XTerm, distinct Chromium replacement, Chromium modal transition, and neutral input cleanup under one session lineage.

T: Xvfb 1280x800x24 + Openbox + Chromium + XTerm + Python-Xlib/XTEST. Construction excluded. Formal runs four fresh sessions exactly once from frozen source.

D: PASS only if all 4 sessions contain exactly the five required gates and every gate is true, Chromium+XTerm are present, replacement IDs differ with old gone, modal framebuffer hashes differ, input is neutral, audit/integrity pass, formal1/reruns0/replacements0/tuning0.

C: fixture mechanics are not controller correctness or task success; XTerm and Chromium internal modal are limited domains; WM behavior is environment-specific.

U: no model/task/recovery/speed/token/human-tempo/cross-backend claim.
