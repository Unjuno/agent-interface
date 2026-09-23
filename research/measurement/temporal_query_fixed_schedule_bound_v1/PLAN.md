# #1633 Temporal fixed-schedule analytic bound

H: four fixed samples chosen before request type cannot cover all later-revealed temporal relations; RECENT_DENSE and LONG_BASELINE are mutually incompatible under budget 4.
T: exact 25ms grid 0..1000; enumerate all C(41,4)=101270 schedules; exact Fraction scoring over four equally weighted classes and 24 anchors; separate auditor; query-conditioned constructive witness.
D: exact enumeration, candidate/auditor agreement, fixed maximum <1, no fixed schedule has positive coverage in all classes, query-conditioned coverage=1, integrity PASS.
C: discrete coverage is not model usefulness; alternate budgets/weights/continuous timing may differ.
U: no model/token/latency/GUI/product claim.
