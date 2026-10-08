# #1441 excluded TRANSIENT_28 boundary construction

Decision: **PASS_T1_A7_BOUNDARY_CONSTRUCTION_ELIGIBLE**.

First/only excluded construction pair under #60 grant bound to source head `9223ce080747378bff6604bf826caf0fd3dcc857`.

- 2/2 fresh private-X11 child sessions exited 0.
- Baseline and candidate both retained the exact frozen transitions `WATCH@28ms -> CLEAR@40ms`.
- The retained CLEAR@40 evidence flush occurred after local authority closure and emitted no input.
- Candidate emitted one pre-handback edge send only; sends beginning at/after 40ms = 0.
- Candidate progress pixels = 100; harm pixels = 0.
- Terminal F8 UP and all cleanup gates passed 2/2.
- Independent corruption controls reject missing CLEAR@40, post-handback send, and repeated edge send.
- Raw decoded JSON SHA-256: `c7dc0616227403f7e2b48a2888e028172d3a1073173603baf210b2d46f2604a2`.

Construction1; formal0; reruns0; replacements0; tuning0. This licenses only the mandatory reread before the separately frozen six-pair formal block.
