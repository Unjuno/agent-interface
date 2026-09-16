# INTEGRATED-REALAPP-FOCUS-RECOVERY-20260917-001
BASE b9dcc5cc456b95ed97d36276ec5557bcae1cad5d
Issue #862

H: byte-pinned #858 adapter can consume a real #855-style read-only X11 receipt after Inkscape->XTerm focus transfer, preserving safe-yield while adding typed focus_mismatch/current B context, without retry/authority.
T: excluded construction on :239; then source-first freeze; formal 8 fresh X11 sessions, 4 stale-context vs 4 real-observe-only, fixed counterorder, one block, reruns 0.
D: exact source identities; Inkscape A -> XTerm B 8/8; stale arm rejected as non-current4/4; real arm typed safe-yield current B4/4; exactly one read query candidate; zero post-rejection submits; authority none; focus unchanged; neutral input; source/audit integrity.
C: this is an integration seam test, not planner/token benefit or corrected action success.
U: one Linux/X11/Inkscape/XTerm fixture; authored focus transfer.
