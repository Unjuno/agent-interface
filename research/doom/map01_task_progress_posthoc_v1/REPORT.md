# MAP01 coverage versus task-relative exit progress — retained diagnostic

Decision: **`COVERAGE_NOT_TASK_PROGRESS_SCOPED / PASS_AUDIT`**.

This diagnostic reuses two already-retained formal blocks and performs no new game/input/model allocation. It was exploratory before GitHub publication, so it is not presented as a prospective formal test.

The exact Freedoom2 WAD contains one MAP01 special-11 exit linedef at index 774, `(184,-632) -> (248,-632)`, with right-side lower texture `SW1COMP` (sector 152) and left sector 156.

For the normal-MAP01 block, the deopt candidate retained a paired median **+8.0 64-unit coverage cells**, but paired median improvement in minimum distance to the exit segment was **0.0**. Candidate was materially closer at the minimum in **0/4** pairs; the minimum occurred at common-prefix step 5 for all four pairs. At the terminal state the candidate was closer in **0/4**, with paired median final-distance improvement **-719.48 map units** (negative = farther away).

For the no-monsters block, paired median coverage was **+8.5 cells**, while paired median minimum-exit improvement was also **0.0**. One pair differed by only ~0.08 map unit, below the 1-unit material diagnostic threshold; materially closer pairs were **0/4**. All pairs again reached their minimum at common-prefix step 5. Candidate final state was closer in **0/4**, paired median final-distance improvement **-730.89 map units**.

Therefore the earlier coverage/revisit PASS claims remain valid at their scoped endpoints, but they must not be described as MAP01 objective progress. The evidence instead points to a missing task-relative progress/subgoal representation. Euclidean distance to the exit is itself incomplete because valid routes may move away from the goal; the next prospective experiment should freeze a semantic subgoal/progress receipt before measurement rather than optimize another local exploration proxy.
