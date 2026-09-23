# #1445 A8 excluded TRANSIENT_28 construction

Decision: **PASS_T1_A8_BOUNDARY_CONSTRUCTION_ELIGIBLE**.

First/only excluded matched pair under #60 grant bound to source head `3a73afc9d6a14ee13266b00a0deca454729466e4`.

- 2/2 fresh private-X11 child sessions exit0.
- Exact WATCH@28 + CLEAR@40 retained in both arms.
- Baseline: authority stop-set +40.196345ms; CLEAR@40 retained +40.406421ms.
- Candidate: authority stop-set +40.024498ms; CLEAR@40 retained +40.172190ms.
- Therefore the boundary evidence flush is observed after authority closure in both arms.
- Candidate's only send begins +0.214810ms; send_begin >=40ms count0.
- Candidate progress100 / harm0; baseline progress0.
- terminal F8 UP and cleanup pass2/2.
- decoded raw SHA-256 `163d77f152e1f689c5dc0b8da0c9b0efd34f665e6d269971deabaf41432522bc`.

construction1 / formal0 / reruns0 / replacements0 / tuning0. Mandatory source/head/lease reread is required before formal.
