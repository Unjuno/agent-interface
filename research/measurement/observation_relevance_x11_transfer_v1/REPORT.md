# #1635 O3 private-X11 relevance transfer

Decision: **PASS_O3_X11_RELEVANCE_TRANSFER_SCOPED**.

The #1583 generation-bound relevance contract was transferred unchanged from synthetic changed-tile histories to exact changed tiles derived from real private-X11 pixels. The fixture is a full-screen 320x240 Tk surface on fresh Xvfb sessions with an exact8x8 tile partition. No perceptual hash, model, provider, network, XTEST, keyboard or pointer input was used.

Formal: one invocation, 12 fresh sessions /72 rows, reruns/replacements/tuning0. Every row had exact 320x240x4 capture bytes and exactly one intended changed tile. Candidate/oracle mismatch0. CURRENT_RELEVANT suppressions0/12; CRITICAL_OUTSIDE suppressions0/12; SHIFT_STALE_HIDDEN suppressions0/12 and full-current fallback12/12; MISSING_RECEIPT full-current fallback12/12. CURRENT_IRRELEVANT suppressions12/12 and FRESH_POST_SHIFT_IRRELEVANT suppressions12/12. The stale-tolerant static comparator falsely suppressed all12 stale-shift rows.

The two safe suppression classes avoided 8,988 bytes of full-current zlib image payload across24 rows. This is transport evidence only, not model-token savings. Independent audit PASS/errors[]; corruption controls5/5; pre/post formal source SHA list identical; residual Xvfb processes0.

Preformal harness defects are retained in SOURCE_MANIFEST: missing XAUTHORITY before rows; same-process Tk/Xvfb teardown XIO before rows; and an Xlib stdout warning ahead of child JSON. All were repaired before source freeze by process-isolated sessions, mode-0600 empty XAUTHORITY under Xvfb -ac, and warning-tolerant child parsing. No scientific schedule or gate changed.

Scope: one deterministic Tk fixture whose relevance truth is authored. This establishes a real-pixel transfer of stale-map safety and demonstrates nonzero safe suppression opportunity; it does not establish relevance inference quality, natural GUI suppression rate, token savings or production runtime behavior.
