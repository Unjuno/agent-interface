# Reservation

TASK: TEMPORAL-BUFFER-X11-CAPTURE-OVERHEAD-20260918-004
PREDECESSORS: #1045 A1 STOPPED_OUTER_ORCHESTRATION_TIMEOUT; #1053 A2 STOPPED_EXTERNAL_EXECUTION_TIMEOUT; #1057 A3 HOLD_EXECUTION_TRANSPORT_UNAVAILABLE_BEFORE_FORMAL
BASE: f596f106a91b510053126f9986ee59a7ed605cf9
BRANCH: research/temporal-buffer-x11-capture-overhead-a4-20260918-004
STATUS: RESERVED_BEFORE_EXECUTION

Fresh A4 allocation. Scientific conditions/gates remain unchanged. Outer execution transport only: launch exactly one detached supervisor process, record its PID, and poll that same PID/status sentinel to completion. No predecessor partial-row pooling.
