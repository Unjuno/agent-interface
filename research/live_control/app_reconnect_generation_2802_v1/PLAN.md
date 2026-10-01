# #2802 Allocation 06 — reconnect generation boundary

## H
A temporal obligation anchored in one producer generation must not be implicitly satisfied by events from a restarted producer generation merely because labels and numeric timestamps are plausible. A generation-bound candidate yields UNKNOWN_GENERATION on cross-generation or missing-generation evidence, while a fresh post-reconnect A→B obligation can satisfy normally.

## T
Six scenarios ×3 cyclic repetitions =18 cases using actual separate producer subprocesses. SAME_PROCESS_AB and LATE_SAME_PROCESS_B use one process. RECONNECT_CROSS_B, RECONNECT_CROSS_AB, FRESH_AFTER_RECONNECT, MISSING_GENERATION_B use two sequential producer processes with distinct PIDs; reconnect scenarios use distinct generation IDs. Source bound1s; late control delays B1.2s. Candidate sees only emitted rows. One formal invocation after construction and GitHub source/gate freeze.

## D
PASS_RECONNECT_GENERATION_BOUNDARY_SCOPED requires18/18 rows; all child exits0; expected candidate SATISFIED6 / EXPIRED3 / UNKNOWN_GENERATION9; unsafe timestamp-only comparator SATISFIED in all6 RECONNECT_CROSS_B/RECONNECT_CROSS_AB cases and all3 missing-generation cases; distinct producer PIDs in reconnect cases; independent audit errors=[] and8/8 controls reject; no retry/replacement/tuning.

## C
Trusted local producer explicitly supplies generation IDs; process restart is serialized. Generation identity is cooperative metadata, not authentication. A fresh obligation begins only on a new A; no automatic state migration is tested.

## U
Sequence wrap within one generation, generation-ID reuse/forgery, concurrent reconnect, dropped bytes, multi-producer ordering, cross-host clocks, GUI/model/task benefit, input authority, reliability rates and production promotion are untested.
