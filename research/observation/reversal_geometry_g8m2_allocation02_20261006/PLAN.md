# #4387 — unequal-interval three-sample reversal applicability

H: The existing full-displacement heuristic can emit a wrong singleton direction under unequal source intervals despite each point remaining within the declared ±1 px bound. A continuous feasible-set solver over the same three observations returns a direction only when all compatible constant/one-reversal worlds agree.

T: Exact finite matrix: six (newest, preceding) interval pairs in ms: (80,15),(15,80),(120,20),(20,120),(60,140),(140,60); two post directions; constant plus reversal ages 2,17,55,105,190 ms; five fixed 3-point error patterns in {0,±0.75 px}. 360 rows. Known speed 73 px/s; point error bound ±1 px; exact rational arithmetic. Compare unchanged legacy float heuristic, exact-rational transcription, and continuous feasible-direction set. One formal process, no rerun/tuning.

D: PASS_UNEQUAL_INTERVAL_APPLICABILITY_SCOPED iff 360 rows complete; at least one legacy wrong direction; rational legacy exactly matches float legacy; true direction belongs to every feasible set; feasible-set singleton is never wrong and is informative at least once; at least one identical-payload opposite-direction witness exists; independent auditor agrees on all rows.

C: This is a favorable known-speed, at-most-one-reversal model. UNKNOWN is not success. Finite directed counts are not operational rates. A result at newest source time does not imply later action-time validity.

U: No GUI/input/model/provider, no capture distribution, no performance or product claim. Incorrect speed/error/motion-class assumptions can invalidate both methods.

Integrity note: the originally proposed matrix was accidentally executed during construction before source/gate freeze and is retained as CONSTRUCTION_EXPOSED.* with STOP_WORKFLOW_INTEGRITY_PREEXPOSURE. This allocation uses only the fresh matrix above; no rows are pooled.
