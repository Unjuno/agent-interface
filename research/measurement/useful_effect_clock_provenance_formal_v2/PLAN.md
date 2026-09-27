# Useful-effect clock provenance formal v2
TASK: USEFUL-EFFECT-CLOCK-PROVENANCE-FORMAL-20260917-002
BASE: 8d77de3b16483652e729e1f3676019692bb58ea8
H: exact merged #1004 candidate preserves same-clock #988 classification and fails closed on missing/mismatched clock provenance on a fresh corpus.
T: exact candidate blob b8e35581e..., independent oracle, seed100420260917002, 180000 fresh records in 5 frozen strata, 13 boundary/malformed controls, exactly one formal invocation.
D: PASS only if 180000/180000 oracle equality, same-clock parent mismatches0, cross/missing clock bound promotions0, controls13/13, side effects0, audit/corruption pass, reruns0.
C: matching labels do not prove clocks truly comparable; measured cross-process relation is separate.
U: synthetic integer-time evidence only; no live X11/application-effect claim.
