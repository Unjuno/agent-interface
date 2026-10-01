# READINESS-CURRENTNESS-AFUNIX-COMPOSITION-20260918-001

H: Extend the exact #1179 current-evidence record with only readiness generation/state. A per-action composite guard should reject readiness-only stale/ABA evidence while preserving #1179 AF_UNIX engineering gates.

T: Standard-library disposable container. Fixed 66-byte BLAKE2b record; 50 ms freshness; strict seq. One excluded hand-authored construction, then source-first freeze/readback, ownership reread, and one formal invocation over 240,000 matched records (120k READY/VALID;30k nonready-only;30k ABA old generation;20k HARD;20k AMBIG;20k fresh post-transition READY). Same authored bytes go through in-process and persistent AF_UNIX GET validation. CURRENTNESS_ONLY is the negative discriminator.

D: PASS only on candidate/oracle mismatch0; readiness stale/ABA effects0; fresh effects>0; HARD/AMBIG effects0; >=20k negative stale-effect witnesses; socket p95<=1ms,p99<=2ms, median socket-inproc<=0.5ms; record<=80 bytes; no readiness authority; integrity/corruption/invocation gates pass. Timing-only failure => HOLD_COMPOSITE_GUARD_TOO_SLOW.

C: A production ABI may unify epochs; this experiment isolates semantic necessity and local IPC cost only.

U: Synthetic/local-IPC composition only. No model/X11/task/production claim. Formal1/reruns0.
