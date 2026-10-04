# T1 STOP — main advanced before candidate

Allocation `OWNER-KEYUP-TIMESTAMP-ORDER-5156-T1-20261004-01` was prospectively registered on Issue #5156 comment 5975275995 against frozen main `4ca1db66b6adcb4ea15fc3c744315ad39a87749e`.

Before any candidate invocation, a fresh remote read observed main at `96f7041fe6b3eb71127ac4eca0ed31d313c29ad2`. The frozen analyzer blob was unchanged (`f3d5fe315df8f4296351f1a5fc666d50ecaa6745`), but the main-advance gate still applies.

Disposition: `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`. Candidate=0; auditor=0; retries=0. No scientific result is claimed. The frozen inputs and source remain unchanged. A successor requires a new allocation and additive path.
